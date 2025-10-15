# Python built-in packages
import os
from datetime import datetime
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

# Third-party packages
import pandas as pd
from dateutil.relativedelta import *
from sqlalchemy import Engine, create_engine, text


class DetDatabase:
    """
    A class to easily interact with the DET database, including fetching and processing data.
    """

    def __init__(self, engine: Engine = None, driver: str = "ODBC Driver 18 for SQL Server"):
        """
        Constructor method.

        Args:
            engine: Instance of SQLAlchemy engine. If None, the instance is automatically
                initialized.
            driver: ODBC driver
        """
        # Only allow object creation if mandatory environment variables exist
        DetDatabase.check_environment_variables()

        self.driver = driver
        self.engine = engine if engine is not None else self.initialize_engine()

    @staticmethod
    def check_environment_variables():
        """
        Checks if environment variables needed by the class are defined.

        Raises:
            EnvironmentError: Raises an error if environment variables are not defined
        """
        required_env_vars = [
            dict(name="DET_DB_NAME", value=None, description="Database name"),
            dict(name="DET_DB_SERVER", value=None, description="Server name"),
            dict(name="DET_DB_USERNAME", value=None, description="Username"),
            dict(name="DET_DB_PASSWORD", value=None, description="Password"),
        ]
        available_env_vars = os.environ
        for d in required_env_vars:
            if d["name"] not in available_env_vars:
                required_env_vars_names = [x["name"] for x in required_env_vars]
                required_env_vars_str = ", ".join(f"'{x}'" for x in required_env_vars_names)
                raise EnvironmentError(
                    f"The DetDatabase class requires the following environment variables: "
                    f"{required_env_vars_str}. Environment variable '{d['name']}' "
                    f"(description: '{d['description']}') not found."
                )

    def initialize_engine(self) -> Engine:
        """
        Initializes the SQLAlchemy engine.

        Returns:
            Instance of SQLAlchemy engine
        """
        # Create the connection string
        connection_str = (
            f"DRIVER={self.driver};"
            f"SERVER={os.getenv('DET_DB_SERVER')};"
            f"DATABASE={os.getenv('DET_DB_NAME')};"
            f"UID={os.getenv('DET_DB_USERNAME')};"
            f"PWD={quote_plus(os.getenv('DET_DB_PASSWORD'))}"
        )
        url = quote_plus(connection_str)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={url}")
        return engine

    def terminate_engine(self):
        """Disconnects the SQLAlchemy engine and releases all underlying resources."""
        self.engine.dispose()

    def query_db(self, query: str) -> pd.DataFrame:
        """
        Short utility method to make an SQL query to the database.

        Args:
            query: SQL query

        Returns:
            Dataframe containing the queried data

        Raises:
            Exception: Raises an error if the SQL query fails
        """
        try:
            df = pd.read_sql_query(query, con=self.engine)
        except Exception as e:
            # If query fails, close connection before raising the error
            self.terminate_engine()
            raise

        return df

    @staticmethod
    def get_table_name(def_key: str) -> str:
        """
        Gets the name of a database table, according to the following logic:
            1) First, try to get the table name from the corresponding environment variable.
            2) If the environment variable is not defined, revert to the default table name.

        Args:
            def_key: Definitions dictionary key corresponding to the desired table

        Returns:
            Database table name
        """
        definition = DetDatabaseDefinitions.DEFINITIONS[def_key]
        table = os.getenv(definition["env_variable"])
        if table is None:
            table = definition["default_table_name"]
        return table

    def load_entsoe_day_ahead_spot_prices(
        self,
        commodity_name: str,
        start_trading_date: datetime = None,
        end_trading_date: datetime = None,
        start_delivery_date: datetime = None,
        end_delivery_date: datetime = None,
        columns: list = None,
        process_data: bool = True,
        timezone_aware_dates: bool = False,
    ) -> pd.DataFrame:
        """
        Loads entsoe day-ahead spot prices from the database.

        Args:
            commodity_name: Commodity name (as defined in the [META].[Commodity] database table)
            start_trading_date: Start trading date
            end_trading_date: End trading date
                Note: The user should provide either 'start_trading_date' and 'end_trading_date',
                or 'start_delivery_date' and 'end_delivery_date'.
            start_delivery_date: Delivery start date. The start datetime is included in the
                filtering (i.e. delivery dates >= start_date).
            end_delivery_date: Delivery end date. The end datetime is excluded from the filtering
                (i.e. delivery dates < end_date).
                Note: The user should provide either 'start_trading_date' and 'end_trading_date',
                or 'start_delivery_date' and 'end_delivery_date'.
            columns: Requested database table columns. Set columns=["*"] (i.e. as list) to get
                all columns.
            process_data: Indicates if data should be processed convert to standardized format
            timezone_aware_dates: If true, returns all dates as timezone-aware. Otherwise,
                returns them as timezone-naive.

        Returns:
            Dataframe containing day-ahead spot prices

        Raises:
            ValueError: Raises an error if input arguments 'columns' and 'process_data' are not
                compatible
            ValueError: Raises an error if the combination of trading dates and delivery dates
                is not valid.
            ValueError: Raises an error if no price data is found for user inputs
        """
        # Input validation
        if process_data and columns is not None:
            raise ValueError(
                "Input argument 'process_data' can only be true if input argument 'columns' "
                "is None."
            )
        if not (
            start_trading_date is not None
            and end_trading_date is not None
            and start_delivery_date is None
            and end_delivery_date is None
        ) and not (
            start_trading_date is None
            and end_trading_date is None
            and start_delivery_date is not None
            and end_delivery_date is not None
        ):
            raise ValueError(
                "Either 'start_trading_date' and 'end_trading_date', or 'start_delivery_date' "
                "and 'end_delivery_date' should be provided."
            )

        # Set default column values
        if columns is None:
            columns = ["DateTime(UTC)", "MapCode", "Price(Currency/MWh)", "Currency"]

        # Always add delivery date column
        if "DateTime(UTC)" not in columns and columns != ["*"]:
            columns.append("DateTime(UTC)")

        # Convert columns from list to string
        if len(columns) == 1:
            columns_str = str(columns[0])
        else:
            columns_str = f"[{'], ['.join(columns)}]"

        # Get commodity information (map code and local timezone)
        # Note: The local timezone is important because ENTSOE provides all prices in the UTC
        # timezone. We first convert the dates from UTC to the local timezone, and then filter
        # for the requested delivery period.
        commodity_info = self.get_commodity_info(
            filter_column="Name",
            filter_value=commodity_name,
            info_columns=["Timezone", "EntsoeMapCode"],
        )
        map_code = commodity_info["EntsoeMapCode"]
        timezone = commodity_info["Timezone"]

        # Convert start trading date to start delivery date
        if start_trading_date is not None:
            start_trading_date = pd.Timestamp(start_trading_date).floor("D")
            start_delivery_date = start_trading_date + relativedelta(days=1)

        # Convert start delivery date from local timezone to UTC and string
        start_delivery_date = start_delivery_date.replace(tzinfo=ZoneInfo(timezone))
        start_delivery_date = start_delivery_date.astimezone(ZoneInfo("UTC"))
        start_date_str = start_delivery_date.strftime("%Y-%m-%d %H:%M:%S")

        # Convert end trading date to end delivery date
        if end_trading_date is not None:
            end_trading_date = pd.Timestamp(end_trading_date).floor("D")
            end_delivery_date = end_trading_date + relativedelta(days=2)

        # Convert end date to UTC and string
        end_delivery_date = end_delivery_date.replace(tzinfo=ZoneInfo(timezone))
        end_delivery_date = end_delivery_date.astimezone(ZoneInfo("UTC"))
        end_date_str = end_delivery_date.strftime("%Y-%m-%d %H:%M:%S")

        # Query db
        table = DetDatabase.get_table_name("entsoe_day_ahead_spot_price")
        query = (
            f"SELECT {columns_str} FROM {table} "
            f"WHERE MapCode='{map_code}' "
            f"AND [DateTime(UTC)]>='{start_date_str}' "
            f"AND [DateTime(UTC)]<'{end_date_str}' "
        )
        df = self.query_db(query)

        if df.empty:
            raise ValueError("No price data found for user-defined inputs.")

        # Sort data by delivery date
        df.sort_values(
            by=["DateTime(UTC)"], axis=0, ascending=True, inplace=True, ignore_index=True
        )

        # Convert date columns to timezone-aware dates
        cols_date_utc = ["DateTime(UTC)", "UpdateTime(UTC)", "InsertionTimestamp"]
        for c in cols_date_utc:
            if c in df.columns:
                df[c] = df[c].dt.tz_localize("UTC")

        # Add column with delivery date expressed in local timezone
        df[f"DateTime({timezone})"] = df["DateTime(UTC)"].dt.tz_convert(timezone)

        if not timezone_aware_dates:
            cols_date_all = cols_date_utc + [f"DateTime({timezone})"]
            for c in cols_date_all:
                if c in df.columns:
                    df[c] = df[c].dt.tz_localize(None)

        # Process raw data and convert it to standardized format
        if process_data:
            df = DetDatabase.process_day_ahead_spot_prices(df, commodity_name, timezone)

        return df

    @staticmethod
    def process_day_ahead_spot_prices(
        df_in: pd.DataFrame, commodity_name: str, timezone: str
    ) -> pd.DataFrame:
        """
        Processes day-ahead spot prices and converts from ENTSOE format to standardized format.

        Args:
            df_in: Dataframe containing day-ahead spot prices
            commodity_name: Commodity name (as defined in the [META].[Commodity] database table)
            timezone: Timezone of the power country/region

        Returns:
            Processed dataframe containing day-ahead spot prices
        """
        df_in.reset_index(drop=True, inplace=True)

        # Initialize output dataframe
        df_out = pd.DataFrame()

        # Set commodity name
        df_out["CommodityName"] = [commodity_name] * df_in.shape[0]

        # Set trading date
        trading_date = [d - relativedelta(days=1, hour=0) for d in df_in[f"DateTime({timezone})"]]
        df_out["TradingDate"] = trading_date

        # Set delivery start date
        df_out["DeliveryStart"] = df_in[f"DateTime({timezone})"]

        # Set delivery end date
        delivery_end = [d + relativedelta(hours=1) for d in df_in[f"DateTime({timezone})"]]
        df_out["DeliveryEnd"] = delivery_end

        # Set tenor
        df_out["Tenor"] = "Spot"

        # Set price
        df_out["Price"] = df_in["Price(Currency/MWh)"].values

        return df_out

    def load_entsoe_imbalance_prices(
        self,
        commodity_name: str,
        start_trading_date: datetime = None,
        end_trading_date: datetime = None,
        start_delivery_date: datetime = None,
        end_delivery_date: datetime = None,
        columns: list = None,
        process_data: bool = True,
        timezone_aware_dates: bool = False,
    ) -> pd.DataFrame:
        """
        Loads entsoe imbalance prices from the database.

        Args:
            commodity_name: Commodity name (as defined in the [META].[Commodity] database table)
            start_trading_date: Start trading date
            end_trading_date: End trading date
                Note: The user should provide either 'start_trading_date' and 'end_trading_date',
                or 'start_delivery_date' and 'end_delivery_date'.
            start_delivery_date: Delivery start date. The start datetime is included in the
                filtering (i.e. delivery dates >= start_date).
            end_delivery_date: Delivery end date. The end datetime is excluded from the filtering
                (i.e. delivery dates < end_date).
                Note: The user should provide either 'start_trading_date' and 'end_trading_date',
                or 'start_delivery_date' and 'end_delivery_date'.
            columns: Requested database table columns. Set columns=["*"] (i.e. as list) to get
                all columns.
            process_data: Indicates if data should be processed convert to standardized format
            timezone_aware_dates: If true, returns all dates as timezone-aware. Otherwise,
                returns them as timezone-naive.

        Returns:
            Dataframe containing imbalance prices

        Raises:
            ValueError: Raises an error if input arguments 'columns' and 'process_data' are not
                compatible
            ValueError: Raises an error if the combination of trading dates and delivery dates
                is not valid.
            ValueError: Raises an error if no price data is found for user inputs
        """
        # Input validation
        if process_data and columns is not None:
            raise ValueError(
                "Input argument 'process_data' can only be true if input argument 'columns' "
                "is None."
            )
        if not (
            start_trading_date is not None
            and end_trading_date is not None
            and start_delivery_date is None
            and end_delivery_date is None
        ) and not (
            start_trading_date is None
            and end_trading_date is None
            and start_delivery_date is not None
            and end_delivery_date is not None
        ):
            raise ValueError(
                "Either 'start_trading_date' and 'end_trading_date', or 'start_delivery_date' "
                "and 'end_delivery_date' should be provided."
            )

        # Set default column values
        if columns is None:
            columns = [
                "DateTime(UTC)",
                "MapCode",
                "PositiveImbalancePrice",
                "NegativeImbalancePrice",
                "Currency",
            ]

        # Always add delivery date column
        if "DateTime(UTC)" not in columns and columns != ["*"]:
            columns.append("DateTime(UTC)")

        # Convert columns from list to string
        if len(columns) == 1:
            columns_str = str(columns[0])
        else:
            columns_str = f"[{'], ['.join(columns)}]"

        # Get commodity information (map code and local timezone)
        # Note: The local timezone is important because ENTSOE provides all prices in the UTC
        # timezone. We first convert the dates from UTC to the local timezone, and then filter
        # for the requested delivery period.
        commodity_info = self.get_commodity_info(
            filter_column="Name",
            filter_value=commodity_name,
            info_columns=["Timezone", "EntsoeMapCode"],
        )
        map_code = commodity_info["EntsoeMapCode"]
        timezone = commodity_info["Timezone"]

        # Convert start trading date to start delivery date
        if start_trading_date is not None:
            start_delivery_date = pd.Timestamp(start_trading_date).floor("D")

        # Convert start delivery date from local timezone to UTC and string
        start_delivery_date = start_delivery_date.replace(tzinfo=ZoneInfo(timezone))
        start_delivery_date = start_delivery_date.astimezone(ZoneInfo("UTC"))
        start_date_str = start_delivery_date.strftime("%Y-%m-%d %H:%M:%S")

        # Convert end trading date to end delivery date
        if end_trading_date is not None:
            end_delivery_date = pd.Timestamp(end_trading_date).floor("D") + relativedelta(days=1)

        # Convert end date to UTC and string
        end_delivery_date = end_delivery_date.replace(tzinfo=ZoneInfo(timezone))
        end_delivery_date = end_delivery_date.astimezone(ZoneInfo("UTC"))
        end_date_str = end_delivery_date.strftime("%Y-%m-%d %H:%M:%S")

        # Query db
        table = DetDatabase.get_table_name("entsoe_imbalance_price")
        query = (
            f"SELECT {columns_str} FROM {table} "
            f"WHERE MapCode='{map_code}' "
            f"AND [DateTime(UTC)]>='{start_date_str}' "
            f"AND [DateTime(UTC)]<'{end_date_str}' "
        )
        df = self.query_db(query)

        if df.empty:
            raise ValueError("No price data found for user-defined inputs.")

        # Sort data by delivery date
        df.sort_values(
            by=["DateTime(UTC)"], axis=0, ascending=True, inplace=True, ignore_index=True
        )

        # Convert date columns to timezone-aware dates
        cols_date_utc = ["DateTime(UTC)", "UpdateTime(UTC)", "InsertionTimestamp"]
        for c in cols_date_utc:
            if c in df.columns:
                df[c] = df[c].dt.tz_localize("UTC")

        # Add column with delivery date expressed in local timezone
        df[f"DateTime({timezone})"] = df["DateTime(UTC)"].dt.tz_convert(timezone)

        if not timezone_aware_dates:
            cols_date_all = cols_date_utc + [f"DateTime({timezone})"]
            for c in cols_date_all:
                if c in df.columns:
                    df[c] = df[c].dt.tz_localize(None)

        # Process raw data and convert it to standardized format
        if process_data:
            df = DetDatabase.process_imbalance_prices(df, commodity_name, timezone)

        return df

    @staticmethod
    def process_imbalance_prices(
        df_in: pd.DataFrame, commodity_name: str, timezone: str
    ) -> pd.DataFrame:
        """
        Processes imbalance prices and converts from ENTSOE format to standardized format.

        Args:
            df_in: Dataframe containing imbalance prices
            commodity_name: Commodity name (as defined in the [META].[Commodity] database table)
            timezone: Timezone of the power country/region

        Returns:
            Processed dataframe containing imbalance prices
        """
        df_in.reset_index(drop=True, inplace=True)

        # Initialize output dataframe
        df_out = pd.DataFrame()

        # Set commodity name
        df_out["CommodityName"] = [commodity_name] * df_in.shape[0]

        # Set trading date
        df_out["TradingDate"] = df_in[f"DateTime({timezone})"].dt.floor("D")

        # Set delivery start date
        df_out["DeliveryStart"] = df_in[f"DateTime({timezone})"]

        # Set delivery end date
        delivery_end = [d + relativedelta(minutes=15) for d in df_in[f"DateTime({timezone})"]]
        df_out["DeliveryEnd"] = delivery_end

        # Set tenor
        df_out["Tenor"] = "Imbalance"

        # Set price
        df_out["PositiveImbalancePrice"] = df_in["PositiveImbalancePrice"].values
        df_out["NegativeImbalancePrice"] = df_in["NegativeImbalancePrice"].values

        return df_out

    def load_futures_eod_settlement_prices(
        self,
        commodity_name: str,
        start_trading_date: datetime,
        end_trading_date: datetime,
        tenors: list,
        delivery_type: str,
        columns: list = None,
        timezone_aware_dates: bool = False,
    ) -> pd.DataFrame:
        """
        Loads futures end-of-day settlement prices from the database, over a user-defined range
        of trading dates.

        Args:
            commodity_name: Commodity name (as defined in the [META].[Commodity] database table)
            start_trading_date: Start trading date
            end_trading_date: End trading date
            tenors: Product tenors (e.g. "Month", "Quarter", "Year")
            delivery_type: Delivery type ("Base", "Peak", "Offpeak")
            columns: Requested database table columns. Set columns=["*"] (i.e. as list) to get
                all columns.
            timezone_aware_dates: If true, returns all dates as timezone-aware. Otherwise,
                returns them as timezone-naive.

        Returns:
            Dataframe containing futures end-of-day settlement prices

        Raises:
            ValueError: Raises an error if no price data is found for user inputs
        """
        # Set default column values
        if columns is None:
            columns = ["*"]

        # Convert columns from list to string
        if len(columns) == 1:
            columns_str = str(columns[0])
        else:
            columns_str = f"[{'], ['.join(columns)}]"

        # Convert tenors from list to string
        tenors_str = f"({' ,'.join([repr(item) for item in tenors])})"

        # Convert dates from datetime to string
        start_trading_date_str = start_trading_date.strftime("%Y-%m-%d")
        end_trading_date_str = end_trading_date.strftime("%Y-%m-%d")

        # Query db
        table = DetDatabase.get_table_name("futures_tt")
        query = (
            f"SELECT {columns_str} FROM {table} "
            f"WHERE CommodityName='{commodity_name}' "
            f"AND TradingDate>='{start_trading_date_str}' "
            f"AND TradingDate<='{end_trading_date_str}' "
            f"AND Tenor IN {tenors_str} "
            f"AND DeliveryType='{delivery_type}'"
        )
        df = self.query_db(query)

        if df.empty:
            raise ValueError("No price data found for user-defined inputs.")

        # Sort data
        df.sort_values(
            by=["TradingDate", "DeliveryStart", "DeliveryEnd"],
            axis=0,
            ascending=True,
            inplace=True,
            ignore_index=True,
        )

        # Convert dates from datetime.date to pd.Timestamp
        cols_date = ["TradingDate", "DeliveryStart", "DeliveryEnd"]
        for c in cols_date:
            if c in df.columns:
                df[c] = pd.DatetimeIndex(df[c])

        if timezone_aware_dates:
            # Get local timezone
            commodity_info = self.get_commodity_info(
                filter_column="Name", filter_value=commodity_name, info_columns=["Timezone"]
            )
            timezone = commodity_info["Timezone"]

            # Convert timezone-naive to timezone-aware dates
            df["InsertionTimestamp"] = df["InsertionTimestamp"].dt.tz_localize("UTC")
            cols_local_tz = ["TradingDate", "DeliveryStart", "DeliveryEnd"]
            for c in cols_local_tz:
                if c in df.columns:
                    df[c] = df[c].dt.tz_localize(timezone)

        return df

    def load_commodities(self, columns: list = None, conditions: str = None) -> pd.DataFrame:
        """
        General method to load data from the database's commodity table.

        Args:
            columns: Requested database table columns. Set columns=["*"] (i.e. as list) to get
                all columns.
            conditions: Optional conditions to add to SQL query. E.g. "WHERE Name='DutchPower'".

        Returns:
            Table data
        """
        # Set default column values
        if columns is None:
            columns = ["*"]

        # Convert columns from list to string
        if len(columns) == 1:
            columns_str = str(columns[0])
        else:
            columns_str = f"[{'], ['.join(columns)}]"

        # Query db
        table = DetDatabase.get_table_name("commodity")
        query = f"SELECT {columns_str} FROM {table} {conditions}"
        df = self.query_db(query)

        return df

    def get_commodity_info(
        self, filter_column: str, filter_value: str, info_columns: list
    ) -> dict:
        """
        Finds information related to a specific, user-defined commodity.

        Args:
            filter_column: Column used to filter data for one specific commodity
            filter_value: Value used to filter data for one specific commodity
            info_columns: Columns containing the requested information

        Returns:
            A dictionary containing the requested information

        Raises:
            ValueError: Raises an error if match with input filter value is not unique
            ValueError: Raises an error if the input filter value is not found
        """
        # Get commodity information for user-defined filtering criteria
        condition = f"WHERE {filter_column}='{filter_value}'"
        commodity_info = self.load_commodities(columns=info_columns, conditions=condition)

        # Validate response
        if commodity_info.shape[0] > 1:
            raise ValueError(f"More than one match found for {filter_column}={filter_value}.")

        elif commodity_info.shape[0] == 0:
            available_values = self.load_commodities(columns=[filter_column])
            available_values_str = ", ".join(f"'{x}'" for x in available_values[filter_column])
            raise ValueError(
                f"Value {filter_value} not found in column '{filter_column}'. Available values: "
                f"{available_values_str}."
            )

        # Convert dataframe row to dict
        commodity_info = commodity_info.loc[0, :].to_dict()

        return commodity_info

    def load_account_positions(
        self, start_trading_date: datetime, end_trading_date: datetime, columns: list = None
    ) -> pd.DataFrame:
        """
        Loads account positions from the database, over a user-defined range of trading dates.

        Args:
            start_trading_date: Start trading date.
            end_trading_date: End trading date.
            columns: Requested database table columns. Set columns=["*"] (i.e. as list) to get
                all columns.

        Returns:
            Dataframe containing account positions.

        Raises:
            ValueError: Raises an error if no position data is found for user inputs.
        """
        # Set default column values
        if columns is None:
            columns = ["*"]

        # Convert columns from list to string
        if len(columns) == 1:
            columns_str = str(columns[0])
        else:
            columns_str = f"[{'], ['.join(columns)}]"

        # Convert dates from datetime to string
        end_trading_date = pd.Timestamp(end_trading_date).floor("D") + relativedelta(days=1)
        start_trading_date_str = start_trading_date.strftime("%Y-%m-%d")
        end_trading_date_str = end_trading_date.strftime("%Y-%m-%d")

        # Query db
        table = DetDatabase.get_table_name("account_position")
        query = (
            f"SELECT {columns_str} FROM {table} "
            f"WHERE InsertionTimestamp>='{start_trading_date_str}' "
            f"AND InsertionTimestamp<'{end_trading_date_str}'"
        )
        df = self.query_db(query)

        # Assert data
        if df.empty:
            raise ValueError("No account position data found for user-defined inputs.")

        # Sort data and convert dates from datetime.date to pd.Timestamp
        if "InsertionTimestamp" in df.columns:
            df.sort_values(
                by=["InsertionTimestamp"],
                axis=0,
                ascending=True,
                inplace=True,
                ignore_index=True,
            )
            df["InsertionTimestamp"] = pd.DatetimeIndex(df["InsertionTimestamp"])

        return df

    def load_instruments(self, identifiers: list, columns: list = None) -> pd.DataFrame:
        """
        Loads instrument data based on identifier (of account positions) from the database.

        Args:
            identifiers: Instrument identifiers (of account positions).
            columns: Requested database table columns. Set columns=["*"] (i.e. as list) to get
                all columns.

        Returns:
            Dataframe containing instrument data.

        Raises:
            ValueError: Raises an error if no instrument data is found for user inputs.
        """
        # Set default column values
        if columns is None:
            columns = ["*"]

        # Convert columns from list to string
        if len(columns) == 1:
            columns_str = str(columns[0])
        else:
            columns_str = f"[{'], ['.join(columns)}]"

        # Convert tenors from list to string
        identifiers_str = ", ".join(f"'{i}'" for i in identifiers)

        # Query db
        table = DetDatabase.get_table_name("instrument")
        query = f"SELECT {columns_str} FROM {table} WHERE [id] IN ({identifiers_str})"
        df = self.query_db(query)

        # Assert data
        if df.empty:
            raise ValueError("No instrument data found for user-defined inputs.")

        return df

    def load_eex_eod_prices(
        self,
        product_code: str,
        start_trading_date: datetime,
        end_trading_date: datetime,
        columns: list = None,
    ) -> pd.DataFrame:
        """
        Loads futures end-of-day EEX prices from the database, over a user-defined range of trading
        dates.

        Args:
            product_code: Product code format indicating commodity, tenor and delivery type as
                defined in the EEX.EODPrice DET database. Assumed product code format do not
                include other product code format (i.e. DEBW and DEBWE do not co-exist)
            start_trading_date: Start trading date.
            end_trading_date: End trading date.
            columns: Requested database table columns. Set columns=["*"] (i.e. as list) to get
                all columns.

        Returns:
            Dataframe containing EEX futures end-of-day prices.

        Raises:
            ValueError: Raises an error if no price data is found for user inputs.
        """
        # Set default column values
        if columns is None:
            columns = ["*"]
        else:
            # Assert required columns
            columns = list(
                set(columns)
                | {"TradingDate", "Product", "Delivery Start", "Delivery End", "Settlement Price"}
            )

        # Convert columns from list to string
        if len(columns) == 1:
            columns_str = str(columns[0])
        else:
            columns_str = f"[{'], ['.join(columns)}]"

        # Convert dates from datetime to string
        start_trading_date_str = start_trading_date.strftime("%Y-%m-%d")
        end_trading_date_str = end_trading_date.strftime("%Y-%m-%d")

        # Query db
        table = DetDatabase.get_table_name("futures_eex")
        query = (
            f"SELECT {columns_str} FROM {table} "
            f"WHERE Product LIKE '{product_code}' "
            f"AND TradingDate>='{start_trading_date_str}' "
            f"AND TradingDate<='{end_trading_date_str}'"
        )
        df = self.query_db(query)

        # Assert data
        if df.empty:
            raise ValueError("No price data found for user-defined inputs.")

        # Sort data
        df.sort_values(
            by=["TradingDate", "Delivery Start", "Delivery End"],
            axis=0,
            ascending=True,
            inplace=True,
            ignore_index=True,
        )

        # Convert dates from datetime.date to pd.Timestamp
        cols_date = ["TradingDate", "Delivery Start", "Delivery End"]
        for c in cols_date:
            if c in df.columns:
                df[c] = pd.DatetimeIndex(df[c])

        # Drop duplicates
        df = df.drop_duplicates()

        return df

    def load_forecast_customer_volume(
        self,
        profile: str,
        forecast_date: datetime,
        start_delivery_date: datetime,
        end_delivery_date: datetime,
        local_timezone: str,
        timezone_aware_dates: bool = False,
        columns: list = None,
    ) -> pd.DataFrame:
        """
        Loads customer volume forecasts from the database.

        Args:
            profile: Customer/profile name.
                Note on the 'Portfolio' and 'Portfolioweekend' profiles:
                - Profile names 'Portfolio' and 'Portfolioweekend' refer to the same set of
                    connection points.
                - In the database, the profile name is set to 'Portfolio' when the forecast date
                    is between Monday and Friday.
                - In the database, the profile name is set to 'Portfolioweekend' when the forecast
                    date is Saturday or Sunday.
                - When calling this method, the input argument 'profile' can be set to
                    'PortfolioAll' to automatically let the method switch between 'Portfolio' and
                    'Portfolioweekend', based on the used-input forecast date.
            forecast_date: Date on which customer volume forecast is generated.
            start_delivery_date: First delivery date included.
            end_delivery_date: Last delivery date included.
            local_timezone: Local timezone (needed to account for DST switches).
            timezone_aware_dates: If true, returns all dates as timezone-aware. Otherwise, returns
                them as timezone-naive.
            columns: Requested database table columns. Set columns=["*"] (i.e. as list) to get all
                columns.

        Returns:
            Dataframe containing customer volume forecasts.

        Raises:
            ValueError: Raises an error if no volume forecast data is found for user inputs.
        """
        # Convert profile if set to "PortfolioAll"
        if profile == "PortfolioAll":
            if forecast_date.weekday() > 4:
                profile = "Portfolioweekend"
            else:
                profile = "Portfolio"

        # Convert start delivery date from local timezone to UTC and string
        start_delivery_date = start_delivery_date.replace(tzinfo=ZoneInfo(local_timezone))
        start_delivery_date = start_delivery_date.astimezone(ZoneInfo("UTC"))
        start_date_str = start_delivery_date.strftime("%Y-%m-%d %H:%M:%S")

        # Convert end delivery date form local timezone to UTC and string
        end_delivery_date = pd.Timestamp(end_delivery_date).floor("D") + relativedelta(days=1)
        end_delivery_date = end_delivery_date.replace(tzinfo=ZoneInfo(local_timezone))
        end_delivery_date = end_delivery_date.astimezone(ZoneInfo("UTC"))
        end_date_str = end_delivery_date.strftime("%Y-%m-%d %H:%M:%S")

        # Set default column values
        if columns is None:
            columns = ["*"]

        # Convert columns from list to string
        if len(columns) == 1:
            columns_str = str(columns[0])
        else:
            columns_str = f"[{'], ['.join(columns)}]"

        # Convert dates from datetime to string
        forecast_date_str = forecast_date.strftime("%Y-%m-%d")

        # Query db
        table = DetDatabase.get_table_name("client_volume_forecast")
        query = (
            f"SELECT {columns_str} FROM {table} "
            f"WHERE Profile='{profile}' "
            f"AND ForecastDate='{forecast_date_str}' "
            f"AND Datetime>='{start_date_str}' "
            f"AND Datetime<'{end_date_str}'"
        )
        df = self.query_db(query)

        # Assert data
        if df.empty:
            raise ValueError("No volume forecast data found for user-defined inputs.")

        # Sort data
        sort_cols = ["Profile", "ForecastDate", "Datetime"]
        sort_cols = [c for c in sort_cols if c in df.columns]
        if len(sort_cols) > 0:
            df.sort_values(
                by=sort_cols,
                axis=0,
                ascending=True,
                inplace=True,
                ignore_index=True,
            )

        # Localize, convert and set timezone-(un)aware datetimes
        cols_date = ["ForecastDate", "Datetime", "InsertionTimestamp"]
        for c in cols_date:
            if c in df.columns:
                # Convert from datetime to pandas timestamp
                df[c] = pd.DatetimeIndex(df[c])

                # Convert to timezone-aware dates
                if c == "ForecastDate":
                    df[c] = df[c].dt.tz_localize(local_timezone)
                else:
                    df[c] = df[c].dt.tz_localize("UTC")
                    df[c] = df[c].dt.tz_convert(local_timezone)

                if not timezone_aware_dates:
                    df[c] = df[c].dt.tz_localize(None)

        # Rescale column values
        df["kWh"] = df["kWh"] / 1000

        # Rename columns
        df = df.rename(columns={"kWh": "Volume(MWh)", "Datetime": "DeliveryStart"})

        return df

    def load_customer_day_ahead_auction_bids(
        self,
        client_id: str,
        start_delivery_date: datetime,
        end_delivery_date: datetime,
        local_timezone: str,
        timezone_aware_dates: bool = False,
        columns: list = None,
    ) -> pd.DataFrame:
        """
        Loads customer day-ahead auction bids (volumes and limit prices) from the database.

        Args:
            client_id: Client ID
            start_delivery_date: First delivery date included
            end_delivery_date: Last delivery date included
            local_timezone: Local timezone (needed to account for DST switches)
            timezone_aware_dates: If true, returns all dates as timezone-aware. Otherwise, returns
                them as timezone-naive
            columns: Requested database table columns. Set columns=["*"] (i.e. as list) to get all
                columns

        Returns:
            Dataframe containing customer day-ahead auction bids

        Raises:
            ValueError: Raises an error if no data is found for user inputs
        """
        # Convert start delivery date from local timezone to UTC and string
        start_delivery_date = start_delivery_date.replace(tzinfo=ZoneInfo(local_timezone))
        start_delivery_date = start_delivery_date.astimezone(ZoneInfo("UTC"))
        start_date_str = start_delivery_date.strftime("%Y-%m-%d %H:%M:%S")

        # Convert end delivery date form local timezone to UTC and string
        end_delivery_date = pd.Timestamp(end_delivery_date).floor("D") + relativedelta(days=1)
        end_delivery_date = end_delivery_date.replace(tzinfo=ZoneInfo(local_timezone))
        end_delivery_date = end_delivery_date.astimezone(ZoneInfo("UTC"))
        end_date_str = end_delivery_date.strftime("%Y-%m-%d %H:%M:%S")

        # Set default column values
        if columns is None:
            columns = ["*"]

        # Convert columns from list to string
        if len(columns) == 1:
            columns_str = str(columns[0])
        else:
            columns_str = f"[{'], ['.join(columns)}]"

        # Query db
        table = DetDatabase.get_table_name("client_day_ahead_auction_bids")
        query = (
            f"SELECT {columns_str} FROM {table} "
            f"WHERE ClientId='{client_id}' "
            f"AND DeliveryStart>='{start_date_str}' "
            f"AND DeliveryStart<'{end_date_str}'"
        )
        df = self.query_db(query)

        # Assert data
        if df.empty:
            raise ValueError("No data found for user-defined inputs.")

        # Sort data
        sort_cols = ["ClientId", "InsertionTimestamp", "DeliveryStart"]
        sort_cols = [c for c in sort_cols if c in df.columns]
        if len(sort_cols) > 0:
            df.sort_values(
                by=sort_cols,
                axis=0,
                ascending=True,
                inplace=True,
                ignore_index=True,
            )

        # Localize, convert and set timezone-(un)aware datetimes
        cols_date = ["DeliveryStart", "DeliveryEnd", "InsertionTimestamp"]
        for c in cols_date:
            if c in df.columns:
                # Convert from datetime to pandas timestamp
                df[c] = pd.DatetimeIndex(df[c])

                # Convert to timezone-aware dates
                if c == "InsertionTimestamp":
                    df[c] = df[c].dt.tz_localize(local_timezone)
                else:
                    df[c] = df[c].dt.tz_localize("UTC")
                    df[c] = df[c].dt.tz_convert(local_timezone)

                if not timezone_aware_dates:
                    df[c] = df[c].dt.tz_localize(None)

        return df

    def load_clients(self, columns: list = None, conditions: str = None) -> pd.DataFrame:
        """
        General method to load data from the database's client table.

        Args:
            columns: Requested database table columns. Set columns=["*"] (i.e. as list) to get
                all columns.
            conditions: Optional conditions to add to SQL query. E.g. "WHERE Type='Supplier'".

        Returns:
            Table data
        """
        # Set default column values
        if columns is None:
            columns = ["*"]

        # Convert columns from list to string
        if len(columns) == 1:
            columns_str = str(columns[0])
        else:
            columns_str = f"[{'], ['.join(columns)}]"

        # Query db
        table = DetDatabase.get_table_name("client")
        query = f"SELECT {columns_str} FROM {table} {conditions}"
        df = self.query_db(query)

        return df

    def get_client_info(self, filter_column: str, filter_value: str, info_columns: list) -> dict:
        """
        Finds information related to a specific, user-defined client.

        Args:
            filter_column: Column used to filter data for one specific client
            filter_value: Value used to filter data for one specific client
            info_columns: Columns containing the requested information

        Returns:
            A dictionary containing the requested information

        Raises:
            ValueError: Raises an error if match with input filter value is not unique
            ValueError: Raises an error if the input filter value is not found
        """
        # Get client information for user-defined filtering criteria
        condition = f"WHERE {filter_column}='{filter_value}'"
        client_info = self.load_clients(columns=info_columns, conditions=condition)

        # Validate response
        if client_info.shape[0] > 1:
            raise ValueError(f"More than one match found for {filter_column}={filter_value}.")

        elif client_info.shape[0] == 0:
            available_values = self.load_clients(columns=[filter_column])
            available_values_str = ", ".join(f"'{x}'" for x in available_values[filter_column])
            raise ValueError(
                f"Value {filter_value} not found in column '{filter_column}'. Available values: "
                f"{available_values_str}."
            )

        # Convert dataframe row to dict
        client_info = client_info.loc[0, :].to_dict()

        return client_info

    def add_table(self, df: pd.DataFrame, table_name: str, schema: str):
        """
        Creates a new database table and populates it with the user-input data.

        Args:
            df: Data used to populate the database table
            table_name: Table name
            schema: Schema
        """
        df.to_sql(name=table_name, schema=schema, con=self.engine, if_exists="fail", index=False)

    def remove_table(self, table_name: str, schema: str):
        """
        Deletes a database table.

        Args:
            table_name: Table name
            schema: Schema
        """
        with self.engine.connect() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS [{schema}].[{table_name}]"))
            conn.commit()


class DetDatabaseDefinitions:
    """A class containing some hard-coded definitions related to the DET database."""

    DEFINITIONS = dict(
        commodity=dict(
            env_variable="DET_DB_TABLE_COMMODITY",
            default_table_name="[META].[Commodity]",
        ),
        entsoe_day_ahead_spot_price=dict(
            env_variable="DET_DB_TABLE_ENTSOE_DA",
            default_table_name="[ENTSOE].[DayAheadSpotPrice]",
        ),
        entsoe_imbalance_price=dict(
            env_variable="DET_DB_TABLE_ENTSOE_IB",
            default_table_name="[ENTSOE].[ImbalancePrice]",
        ),
        futures_tt=dict(
            env_variable="DET_DB_TABLE_FUTURES_TT",
            default_table_name="[VW].[EODSettlementPrice]",
        ),
        futures_eex=dict(
            env_variable="DET_DB_TABLE_FUTURES_EEX",
            default_table_name="[EEX].[EODPrice]",
        ),
        account_position=dict(
            env_variable="DET_DB_TABLE_ACCOUNT_POSITION",
            default_table_name="[TT].[AccountPosition]",
        ),
        instrument=dict(
            env_variable="DET_DB_TABLE_INSTRUMENT",
            default_table_name="[TT].[Instrument]",
        ),
        client_volume_forecast=dict(
            env_variable="DET_DB_TABLE_CLIENT_VOLUME_FORECAST",
            default_table_name="[DISP].[ForecastGold]",
        ),
        client_day_ahead_auction_bids=dict(
            env_variable="DET_DB_TABLE_CLIENT_DA_AUCTION_BIDS",
            default_table_name="[TRADE].[ClientBid]",
        ),
        client=dict(
            env_variable="DET_DB_TABLE_CLIENT",
            default_table_name="[META].[Client]",
        ),
    )
