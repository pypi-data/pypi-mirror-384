import json
import logging
from datetime import datetime
from typing import Dict, Any, Union

from mcp.server.fastmcp import FastMCP
from pykrx.stock.stock_api import get_market_ohlcv, get_nearest_business_day_in_a_week, get_market_cap, \
    get_market_fundamental_by_date, get_market_trading_volume_by_date, get_index_ohlcv_by_date
from pykrx.website.krx.market.wrap import get_market_ticker_and_name

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create MCP server (add pykrx dependency)
mcp = FastMCP(
    "kospi-kosdaq-stock-server",
    dependencies=["pykrx"]
)

# Global variable to store ticker information in memory
TICKER_MAP: Dict[str, str] = {}

@mcp.tool()
def load_all_tickers() -> Dict[str, str]:
    """Loads all ticker symbols and names for KOSPI and KOSDAQ into memory.

    Returns:
        Dict[str, str]: A dictionary mapping tickers to stock names.
        Example: {"005930": "삼성전자", "035720": "카카오", ...}
    """
    try:
        global TICKER_MAP

        # If TICKER_MAP already has data, return it
        if TICKER_MAP:
            logging.debug(f"Returning cached ticker information with {len(TICKER_MAP)} stocks")
            return TICKER_MAP

        logging.debug("No cached data found. Loading KOSPI/KOSDAQ ticker symbols")

        # Retrieve data based on today's date
        today = get_nearest_business_day_in_a_week()
        logging.debug(f"Reference date: {today}")

        # get_market_ticker_and_name() returns a Series,
        # where the index is the ticker and the values are the stock names
        kospi_series = get_market_ticker_and_name(today, market="KOSPI")
        kosdaq_series = get_market_ticker_and_name(today, market="KOSDAQ")

        # Convert Series to dictionaries and merge them
        TICKER_MAP.update(kospi_series.to_dict())
        TICKER_MAP.update(kosdaq_series.to_dict())

        logging.debug(f"Successfully stored information for {len(TICKER_MAP)} stocks")
        return TICKER_MAP

    except Exception as e:
        error_message = f"Failed to retrieve ticker information: {str(e)}"
        logging.error(error_message)
        return {"error": error_message}

@mcp.resource("stock://tickers")
def get_ticker_map() -> str:
    """Retrieves the stored ticker symbol-name mapping information."""
    try:
        if not TICKER_MAP:
            return json.dumps({"message": "No ticker information stored. Please run the load_all_tickers() tool first to load ticker information."})

        # Return formatted for better readability
        # result = ["[Ticker Symbol - Stock Name Mapping]"]
        # for ticker, name in TICKER_MAP.items():
        #     result.append(f"- {ticker}: {name}")
        # return "\n".join(result)
        return json.dumps(TICKER_MAP)

    except Exception as e:
      return json.dumps({"error": f"Failed to retrieve ticker information: {str(e)}"})

@mcp.prompt()
def search_stock_data_prompt() -> str:
    """Prompt template for searching stock data."""
    return """
    Step-by-step guide for searching stock data by stock name:

    1. First, load the ticker information for all stocks:
       load_all_tickers()

    2. Check the code of the desired stock from the loaded ticker information:
       Refer to the stock://tickers resource to find the ticker corresponding to the stock name.

    3. Retrieve the desired data using the found ticker:

       Retrieve OHLCV (Open/High/Low/Close/Volume) data:
       get_stock_ohlcv("start_date", "end_date", "ticker", adjusted=True)

       Retrieve market capitalization data:
       get_stock_market_cap("start_date", "end_date", "ticker")

       Retrieve fundamental indicators (PER/PBR/Dividend Yield):
       get_stock_fundamental("start_date", "end_date", "ticker")

       Retrieve trading volume by investor type:
       get_stock_trading_volume("start_date", "end_date", "ticker")

       Retrieve index OHLCV data (KOSPI, KOSDAQ, etc.):
       get_index_ohlcv("start_date", "end_date", "ticker", freq="d")
       - ticker: 1001 for KOSPI, 2001 for KOSDAQ
       - freq: "d" for daily, "m" for monthly, "y" for yearly

    Example) To retrieve data for Samsung Electronics in January 2024:
    1. load_all_tickers()  # Load all tickers
    2. Refer to stock://tickers  # Check Samsung Electronics = 005930
    3. get_stock_ohlcv("20240101", "20240131", "005930")  # Retrieve OHLCV data
       or
       get_stock_market_cap("20240101", "20240131", "005930")  # Retrieve market cap data
       or
       get_stock_fundamental("20240101", "20240131", "005930")  # Retrieve fundamental data
       or
       get_stock_trading_volume("20240101", "20240131", "005930")  # Retrieve trading volume

    Example) To retrieve KOSPI index data for January 2021:
       get_index_ohlcv("20210101", "20210131", "1001", freq="d")  # Daily KOSPI data
    """

@mcp.tool()
def get_stock_ohlcv(fromdate: Union[str, int], todate: Union[str, int], ticker: Union[str, int], adjusted: bool = True) -> Dict[str, Any]:
    """Retrieves OHLCV (Open/High/Low/Close/Volume) data for a specific stock.

    Args:
        fromdate (str): Start date for retrieval (YYYYMMDD)
        todate   (str): End date for retrieval (YYYYMMDD)
        ticker   (str): Stock ticker symbol
        adjusted (bool, optional): Whether to use adjusted prices (True: adjusted, False: unadjusted). Defaults to True.

    Returns:
        DataFrame:
            >> get_stock_ohlcv("20210118", "20210126", "005930")
                            Open     High     Low    Close   Volume
            Date
            2021-01-26  89500  94800  89500  93800  46415214
            2021-01-25  87300  89400  86800  88700  25577517
            2021-01-22  89000  89700  86800  86800  30861661
            2021-01-21  87500  88600  86500  88100  25318011
            2021-01-20  89000  89000  86500  87200  25211127
            2021-01-19  84500  88000  83600  87000  39895044
            2021-01-18  86600  87300  84100  85000  43227951
    """
    # Validate and convert date format
    def validate_date(date_str: Union[str, int]) -> str:
        try:
            if isinstance(date_str, int):
                date_str = str(date_str)
            # Convert if in YYYY-MM-DD format
            if '-' in date_str:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                return parsed_date.strftime('%Y%m%d')
            # Validate if in YYYYMMDD format
            datetime.strptime(date_str, '%Y%m%d')
            return date_str
        except ValueError:
            raise ValueError(f"Date must be in YYYYMMDD format. Input value: {date_str}")

    def validate_ticker(ticker_str: Union[str, int]) -> str:
        if isinstance(ticker_str, int):
            return str(ticker_str)
        return ticker_str

    try:
        fromdate = validate_date(fromdate)
        todate = validate_date(todate)
        ticker = validate_ticker(ticker)

        logging.debug(f"Retrieving stock OHLCV data: {ticker}, {fromdate}-{todate}, adjusted={adjusted}")

        # Call get_market_ohlcv (changed adj -> adjusted)
        df = get_market_ohlcv(fromdate, todate, ticker, adjusted=adjusted)

        # Convert DataFrame to dictionary
        result = df.to_dict(orient='index')

        # Convert datetime index to string and sort in reverse
        sorted_items = sorted(
            ((k.strftime('%Y-%m-%d'), v) for k, v in result.items()),
            reverse=True
        )
        result = dict(sorted_items)

        return result

    except Exception as e:
        error_message = f"Data retrieval failed: {str(e)}"
        logging.error(error_message)
        return {"error": error_message}

@mcp.resource("stock://format-guide")
def get_format_guide() -> str:
    """Provides a guide for date format and ticker symbol input."""
    return """
    [Input Format Guide]
    1. Ticker symbol: 6-digit number (e.g., 005930 - Samsung Electronics)
    2. Date format: YYYYMMDD (e.g., 20240301) or YYYY-MM-DD (e.g., 2024-03-01)

    [Notes]
    - The start date must be earlier than the end date.
    - If adjusted=True, adjusted prices are retrieved; if False, unadjusted prices are retrieved.
    """

@mcp.resource("stock://popular-tickers")
def get_popular_tickers() -> str:
    """Provides a list of frequently queried ticker symbols."""
    return """
    [Frequently Queried Ticker Symbols]
    - 005930: 삼성전자
    - 000660: SK하이닉스
    - 373220: LG에너지솔루션
    - 035420: NAVER
    - 035720: 카카오
    """

@mcp.prompt()
def get_stock_data_prompt() -> str:
    """Prompt template for retrieving stock data."""
    return """
    Please enter the following information to retrieve stock OHLCV data:

    1. Ticker symbol: 6-digit number (e.g., 005930)
    2. Start date: YYYYMMDD format (e.g., 20240101)
    3. End date: YYYYMMDD format (e.g., 20240301)
    4. Adjusted price: True/False (default: True)

    Example) get_stock_ohlcv("20240101", "20240301", "005930", adjusted=True)
    """

@mcp.tool()
def get_stock_market_cap(fromdate: Union[str, int], todate: Union[str, int], ticker: Union[str, int]) -> Dict[str, Any]:
    """Retrieves market capitalization data for a specific stock.

    Args:
        fromdate (str): Start date for retrieval (YYYYMMDD)
        todate   (str): End date for retrieval (YYYYMMDD)
        ticker   (str): Stock ticker symbol

    Returns:
        DataFrame:
            >> get_stock_market_cap("20150720", "20150724", "005930")
                              Market Cap  Volume      Trading Value  Listed Shares
            Date
            2015-07-24  181030885173000  196584  241383636000  147299337
            2015-07-23  181767381858000  208965  259446564000  147299337
            2015-07-22  184566069261000  268323  333813094000  147299337
            2015-07-21  186039062631000  194055  244129106000  147299337
            2015-07-20  187806654675000  128928  165366199000  147299337
    """
    # Validate and convert date format
    def validate_date(date_str: Union[str, int]) -> str:
        try:
            if isinstance(date_str, int):
                date_str = str(date_str)
            # Convert if in YYYY-MM-DD format
            if '-' in date_str:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                return parsed_date.strftime('%Y%m%d')
            # Validate if in YYYYMMDD format
            datetime.strptime(date_str, '%Y%m%d')
            return date_str
        except ValueError:
            raise ValueError(f"Date must be in YYYYMMDD format. Input value: {date_str}")

    def validate_ticker(ticker_str: Union[str, int]) -> str:
        if isinstance(ticker_str, int):
            return str(ticker_str)
        return ticker_str

    try:
        fromdate = validate_date(fromdate)
        todate = validate_date(todate)
        ticker = validate_ticker(ticker)

        logging.debug(f"Retrieving stock market capitalization data: {ticker}, {fromdate}-{todate}")

        # Call get_market_cap
        df = get_market_cap(fromdate, todate, ticker)

        # Convert DataFrame to dictionary
        result = df.to_dict(orient='index')

        # Convert datetime index to string and sort in reverse
        sorted_items = sorted(
            ((k.strftime('%Y-%m-%d'), v) for k, v in result.items()),
            reverse=True
        )
        result = dict(sorted_items)

        return result

    except Exception as e:
        error_message = f"Data retrieval failed: {str(e)}"
        logging.error(error_message)
        return {"error": error_message}

@mcp.tool()
def get_stock_fundamental(fromdate: Union[str, int], todate: Union[str, int], ticker: Union[str, int]) -> Dict[str, Any]:
    """Retrieves fundamental data (PER/PBR/Dividend Yield) for a specific stock.

    Args:
        fromdate (str): Start date for retrieval (YYYYMMDD)
        todate   (str): End date for retrieval (YYYYMMDD)
        ticker   (str): Stock ticker symbol

    Returns:
        DataFrame:
            >> get_stock_fundamental("20210104", "20210108", "005930")
                              BPS        PER       PBR   EPS       DIV   DPS
                Date
                2021-01-08  37528  28.046875  2.369141  3166  1.589844  1416
                2021-01-07  37528  26.187500  2.210938  3166  1.709961  1416
                2021-01-06  37528  25.953125  2.189453  3166  1.719727  1416
                2021-01-05  37528  26.500000  2.240234  3166  1.690430  1416
                2021-01-04  37528  26.218750  2.210938  3166  1.709961  1416
    """
    # Validate and convert date format
    def validate_date(date_str: Union[str, int]) -> str:
        try:
            if isinstance(date_str, int):
                date_str = str(date_str)
            if '-' in date_str:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                return parsed_date.strftime('%Y%m%d')
            datetime.strptime(date_str, '%Y%m%d')
            return date_str
        except ValueError:
            raise ValueError(f"Date must be in YYYYMMDD format. Input value: {date_str}")

    def validate_ticker(ticker_str: Union[str, int]) -> str:
        if isinstance(ticker_str, int):
            return str(ticker_str)
        return ticker_str

    try:
        fromdate = validate_date(fromdate)
        todate = validate_date(todate)
        ticker = validate_ticker(ticker)

        logging.debug(f"Retrieving stock fundamental data: {ticker}, {fromdate}-{todate}")

        # Call get_market_fundamental_by_date
        df = get_market_fundamental_by_date(fromdate, todate, ticker)

        # Convert DataFrame to dictionary
        result = df.to_dict(orient='index')

        # Convert datetime index to string and sort in reverse
        sorted_items = sorted(
            ((k.strftime('%Y-%m-%d'), v) for k, v in result.items()),
            reverse=True
        )
        result = dict(sorted_items)

        return result

    except Exception as e:
        error_message = f"Data retrieval failed: {str(e)}"
        logging.error(error_message)
        return {"error": error_message}

@mcp.tool()
def get_stock_trading_volume(fromdate: Union[str, int], todate: Union[str, int], ticker: Union[str, int]) -> Dict[str, Any]:
    """Retrieves trading volume by investor type for a specific stock.

    Args:
        fromdate (str): Start date for retrieval (YYYYMMDD)
        todate   (str): End date for retrieval (YYYYMMDD)
        ticker   (str): Stock ticker symbol

    Returns:
        DataFrame with columns:
        - Volume (Sell/Buy/Net Buy)
        - Trading Value (Sell/Buy/Net Buy)
        Broken down by investor types (Financial Investment, Insurance, Trust, etc.)
    """
    # Validate and convert date format
    def validate_date(date_str: Union[str, int]) -> str:
        try:
            if isinstance(date_str, int):
                date_str = str(date_str)
            if '-' in date_str:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                return parsed_date.strftime('%Y%m%d')
            datetime.strptime(date_str, '%Y%m%d')
            return date_str
        except ValueError:
            raise ValueError(f"Date must be in YYYYMMDD format. Input value: {date_str}")

    def validate_ticker(ticker_str: Union[str, int]) -> str:
        if isinstance(ticker_str, int):
            return str(ticker_str)
        return ticker_str

    try:
        fromdate = validate_date(fromdate)
        todate = validate_date(todate)
        ticker = validate_ticker(ticker)

        logging.debug(f"Retrieving stock trading volume by investor type: {ticker}, {fromdate}-{todate}")

        # Call get_market_trading_volume_by_date
        df = get_market_trading_volume_by_date(fromdate, todate, ticker)

        # Convert DataFrame to dictionary
        result = df.to_dict(orient='index')

        # Convert datetime index to string and sort in reverse
        sorted_items = sorted(
            ((k.strftime('%Y-%m-%d'), v) for k, v in result.items()),
            reverse=True
        )
        result = dict(sorted_items)

        return result

    except Exception as e:
        error_message = f"Data retrieval failed: {str(e)}"
        logging.error(error_message)
        return {"error": error_message}


@mcp.tool()
def get_index_ohlcv(fromdate: Union[str, int], todate: Union[str, int], ticker: Union[str, int], freq: str = 'd') -> \
Dict[str, Any]:
    """Retrieves OHLCV data for a specific index.

    Args:
        fromdate (str): Start date for retrieval (YYYYMMDD)
        todate   (str): End date for retrieval (YYYYMMDD)
        ticker   (str): Index ticker symbol (e.g., 1001 for KOSPI, 2001 for KOSDAQ)
        freq     (str, optional): d - daily / m - monthly / y - yearly. Defaults to 'd'.

    Returns:
        DataFrame:
            >> get_index_ohlcv("20210101", "20210130", "1001")
                           Open     High      Low    Close       Volume    Trading Value
            Date
            2021-01-04  2874.50  2946.54  2869.11  2944.45  1026510465  25011393960858
            2021-01-05  2943.67  2990.57  2921.84  2990.57  1519911750  26548380179493
            2021-01-06  2993.34  3027.16  2961.37  2968.21  1793418534  29909396443430
            2021-01-07  2980.75  3055.28  2980.75  3031.68  1524654500  27182807334912
            2021-01-08  3040.11  3161.11  3040.11  3152.18  1297903388  40909490005818
    """

    # Validate and convert date format
    def validate_date(date_str: Union[str, int]) -> str:
        try:
            if isinstance(date_str, int):
                date_str = str(date_str)
            if '-' in date_str:
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                return parsed_date.strftime('%Y%m%d')
            datetime.strptime(date_str, '%Y%m%d')
            return date_str
        except ValueError:
            raise ValueError(f"Date must be in YYYYMMDD format. Input value: {date_str}")

    def validate_ticker(ticker_str: Union[str, int]) -> str:
        if isinstance(ticker_str, int):
            return str(ticker_str)
        return ticker_str

    def validate_freq(freq_str: str) -> str:
        valid_freqs = ['d', 'm', 'y']
        if freq_str not in valid_freqs:
            raise ValueError(f"Frequency must be one of {valid_freqs}. Input value: {freq_str}")
        return freq_str

    try:
        fromdate = validate_date(fromdate)
        todate = validate_date(todate)
        ticker = validate_ticker(ticker)
        freq = validate_freq(freq)

        logging.debug(f"Retrieving index OHLCV data: {ticker}, {fromdate}-{todate}, freq={freq}")

        # Call get_index_ohlcv_by_date
        # Note: name_display is set to False to match the pattern of other functions
        df = get_index_ohlcv_by_date(fromdate, todate, ticker, freq=freq, name_display=False)

        # Convert DataFrame to dictionary
        result = df.to_dict(orient='index')

        # Convert datetime index to string and sort in reverse
        sorted_items = sorted(
            ((k.strftime('%Y-%m-%d'), v) for k, v in result.items()),
            reverse=True
        )
        result = dict(sorted_items)

        return result

    except Exception as e:
        error_message = f"Data retrieval failed: {str(e)}"
        logging.error(error_message)
        return {"error": error_message}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
