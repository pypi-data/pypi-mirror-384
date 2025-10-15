import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from typing import List,Union,Any,Dict
import numpy as np
import os
import warnings
from dateutil import parser
import time 



def read_api_key(file_path):

    try:
        with open(file_path, 'r') as f:
            line = f.readline().strip()

            # Ensure the line is not empty and contains an '='
            if not line or '=' not in line:
                print(f"Error: The file '{file_path}' has an invalid format. Expected 'key=value'.")
                return None

            # Split the line at the first '=' to separate key and value
            key, value = line.split('=', 1)

            # Strip any surrounding whitespace from the value
            # and remove any potential quotes if they exist
            api_key = value.strip().strip('"').strip("'")
            
            # Check if the extracted value is empty
            if not api_key:
                print(f"Error: The API key value in '{file_path}' is empty.")
                return None
            
            return api_key

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
        return None

def ohlc_dataframe(data: Union[str, pd.DataFrame], **kwargs) -> pd.DataFrame:
   
    df = None
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    elif isinstance(data, str):
        file_path = data
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at '{file_path}'")

        file_extension = os.path.splitext(file_path)[1].lower()

        # Map file extensions to their corresponding pandas reader functions
        readers = {
            '.csv': pd.read_csv,
            '.tsv': lambda path, **kw: pd.read_csv(path, sep='\t', **kw),
            '.parquet': pd.read_parquet,
            '.pqt': pd.read_parquet,
            '.xls': pd.read_excel,
            '.xlsx': pd.read_excel,
            '.json': pd.read_json,
            '.html': lambda path, **kw: pd.read_html(path, **kw)[0]
        }

        try:
            if file_extension not in readers:
                supported_formats = list(readers.keys())
                raise ValueError(f"Unsupported file type: '{file_extension}'. "
                                 f"Supported formats are: {', '.join(supported_formats)}")

            # Read the DataFrame using the appropriate function
            df = readers[file_extension](file_path, **kwargs)

        except Exception as e:
            print(f"An error occurred while reading the file: {e}")
            raise
    else:
        raise TypeError("Input must be a file path (str) or a pandas DataFrame.")

    ohlc_cols = {'datetime', 'open', 'high', 'low', 'close'}
    current_cols = set(df.columns.str.lower())
    has_ohlc = ohlc_cols.issubset(current_cols)

    if not has_ohlc:
        raise ValueError("DataFrame must contain the columns: 'datetime', 'open', 'high', 'low', 'close'")

    valid_date_formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y %H:%M:%S',
        '%d-%m-%Y %H:%M:%S',
        '%d-%m-%Y %H:%M'
    ]
    
    datetime_series = df['datetime'].copy()
    format_found = False
    
    for fmt in valid_date_formats:
        try:
            
            datetime_series = pd.to_datetime(df['datetime'], format=fmt)
            format_found = True
            break  
        except (ValueError, TypeError):
            continue  

    if not format_found:
        raise ValueError(
            f"Could not convert 'datetime' column to any of the supported formats. "
            f"Supported formats are: {', '.join(valid_date_formats)}"
        )

    # Convert to the datetime format for API
    df['datetime'] = datetime_series.dt.strftime('%Y-%m-%d %H:%M:%S')

    return df

def univariate_dataframe(data: Union[str, pd.DataFrame], **kwargs) -> pd.DataFrame:
       
    df = None
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    elif isinstance(data, str):
        file_path = data
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at '{file_path}'")

        file_extension = os.path.splitext(file_path)[1].lower()

        # Map file extensions to their corresponding pandas reader functions
        readers = {
            '.csv': pd.read_csv,
            '.tsv': lambda path, **kw: pd.read_csv(path, sep='\t', **kw),
            '.parquet': pd.read_parquet,
            '.pqt': pd.read_parquet,
            '.xls': pd.read_excel,
            '.xlsx': pd.read_excel,
            '.json': pd.read_json,
            '.html': lambda path, **kw: pd.read_html(path, **kw)[0]
        }

        try:
            if file_extension not in readers:
                supported_formats = list(readers.keys())
                raise ValueError(f"Unsupported file type: '{file_extension}'. "
                                 f"Supported formats are: {', '.join(supported_formats)}")

            # Read the DataFrame using the appropriate function
            df = readers[file_extension](file_path, **kwargs)

        except Exception as e:
            print(f"An error occurred while reading the file: {e}")
            raise
    else:
        raise TypeError("Input must be a file path (str) or a pandas DataFrame.")

    ohlc_cols = {'datetime', 'value'}
    current_cols = set(df.columns.str.lower())
    has_ohlc = ohlc_cols.issubset(current_cols)

    if not has_ohlc:
        raise ValueError("DataFrame must contain the columns: 'datetime', 'value'")

    valid_date_formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y %H:%M:%S',
        '%d-%m-%Y %H:%M:%S',
        '%d-%m-%Y %H:%M'
    ]
    
    datetime_series = df['datetime'].copy()
    format_found = False
    
    for fmt in valid_date_formats:
        try:
            # Try to convert using a specific format
            datetime_series = pd.to_datetime(df['datetime'], format=fmt)
            format_found = True
            break  # Stop at the first successful format
        except (ValueError, TypeError):
            continue  # Try the next format if this one fails

    if not format_found:
        raise ValueError(
            f"Could not convert 'datetime' column to any of the supported formats. "
            f"Supported formats are: {', '.join(valid_date_formats)}"
        )

    # Convert to the datetime format for API
    df['datetime'] = datetime_series.dt.strftime('%Y-%m-%d %H:%M:%S')

    return df

def dict_to_dataframe(response_dict: dict, datetime_col: str) -> pd.DataFrame:

    if not isinstance(response_dict, dict):
        raise ValueError("There was an issue with the API response. This often happens if your account hasn't been approved after signing up. Reach out to us at team@sumtyme.ai for assistance.")


    datetimes = []
    trends = []

    if not response_dict:
        return pd.DataFrame({datetime_col: [], 'chain_detected': []})

    for timestamp_str, data in response_dict.items():
        if not isinstance(data, dict) or 'chain_detected' not in data:
            raise KeyError(
                f"Invalid structure for timestamp '{timestamp_str}'. "
                "Expected a dictionary with 'chain_detected' key."
            )
        datetimes.append(timestamp_str)
        trends.append(data['chain_detected'])

    df = pd.DataFrame({
        datetime_col: datetimes,
        'chain_detected': trends
    })

    try:
        df[datetime_col] = pd.to_datetime(df[datetime_col])
    except Exception as e:
        raise ValueError(f"Could not convert '{datetime_col}' column to datetime objects: {e}")

    df = df.sort_values(datetime_col).reset_index(drop=True)
    return df

def write_dict_entry_to_csv(data_dict: Dict[str, Any], filepath: str, separator: str = ','):
    
    HARDCODED_HEADERS = ['datetime', 'chain_detected']
    header_line = separator.join(HARDCODED_HEADERS)
    
    file_exists = os.path.exists(filepath)
    file_is_empty = file_exists and os.path.getsize(filepath) == 0
    file_is_new_or_empty = not file_exists or file_is_empty

    try:
        if file_is_new_or_empty:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(header_line + '\n')
            
   
        if not data_dict:
            print("Warning: Input dictionary is empty. Skipping file write.")
            return

        try:
            datetime_str, chain_val = next(iter(data_dict.items()))
        except StopIteration:

            print("Warning: Could not extract key/value pair. Skipping file write.")
            return

        data_row_line = separator.join([str(datetime_str), str(chain_val)])


        with open(filepath, 'a', encoding='utf-8') as file:
            file.write(data_row_line + '\n')

        print(f"Successfully wrote data entry to {filepath}")

    except Exception as e:
        print(f"An error occurred while writing the file: {e}")

class EIPClient:
    
    """
    A python client for interacting with Embedded Intelligence Platform (EIP) by sumtyme.ai.
    """

    SIGNUP = "/signup"

    CAUSAL_OHLC = "/causal-chain/ohlc"
    CAUSAL_OHLC_ENV = "/causal-chain/ohlc-model"

    CAUSAL_UNIV = "/causal-chain/univariate"
    CAUSAL_UNIV_ENV = "/causal-chain/univariate-model"

    def __init__(self, apikey: str = None):
       
        self.base_url = f"https://www.sumtyme.com"

        if apikey is None: # Check if apikey is None
            warnings.warn(
                "To obtain an API key, sign up for an account using the `user_signup` method or contact us at team@sumtyme.ai.",
                UserWarning
            )

            self.api_key = None
            print("EIPClient initialised without API key.")

        else:
            self.api_key = apikey

            if not self.api_key:
                raise ValueError(
                    "API key provided is an empty string."
                )

            print("EIPClient initialised and API key loaded.")


    def send_signup_request(self, path: str, payload: dict) -> dict:

        full_url = f"{self.base_url}{path}"

        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(full_url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
      
            if response.status_code == 200:
                api_key = response_data.get("api_key")
                user_email = response_data.get("email")
                message = response_data.get("message")

                if api_key:
              
                    filename = f"config.txt"
                    with open(filename, "w") as f:
                        text_input = "apikey="+api_key
                        f.write(text_input)
                    print(f"Success: {message}")
                    print(f"API Key for {user_email} saved to {filename}")
                    return {"success": True, "api_key": api_key, "filename": filename}
                else:
                    print(f"Error: Signup successful but no API key found in response. Response: {response_data}")
                    return {"success": False, "message": "API key not found in response"}
            else:
          
                print(f"Unexpected successful response status code: {response.status_code}. Response: {response_data}")
                return {"success": False, "message": "Unexpected successful response"}
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - Response: {response.text}")
            raise
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
            raise
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
            raise
        except json.JSONDecodeError as json_err:
            print(f"Failed to decode JSON response: {json_err} - Response text: {response.text}")
            raise
        except requests.exceptions.RequestException as req_err:
            print(f"An unexpected request error occurred: {req_err}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred in send_signup_request: {e}")
            raise

    def send_post_request(self, path: str, payload: dict) -> dict:

        full_url = f"{self.base_url}{path}"

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        try:
            response = requests.post(full_url, json=payload, headers=headers)
           
            response.raise_for_status()
            response_data = response.json()

            return response_data
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - Response: {response.text}")
            raise
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
            raise
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
            raise
        except json.JSONDecodeError as json_err:
            print(f"Failed to decode JSON response: {json_err} - Response text: {response.text}")
            raise
        except requests.exceptions.RequestException as req_err:
            print(f"An unexpected request error occurred: {req_err}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred in send_post_request: {e}")
            raise

    def user_signup(self, payload: dict)->dict:
        """
        Registers a new user and attempts to retrieve an API key.

        Parameters:
        -----------
        payload : dict
            A dictionary containing user signup information (e.g., 'email', 'password').

        Returns:
        --------
        dict
            A dictionary indicating success/failure, and potentially the API key and filename.
        """
        response_dict = self.send_signup_request(self.SIGNUP, payload)
        return response_dict

    

    @staticmethod
    def _time_series_dict(df: pd.DataFrame, interval: int, interval_unit: str, reasoning_mode: str) -> dict:
       
        # Validate input DataFrame type
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input 'df' must be a pandas DataFrame.")

        # Check for required columns
        required_columns = ['datetime', 'open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            raise KeyError(f"DataFrame is missing required columns: {missing_cols}")
        
        # Ensure 'datetime' column is of datetime type
        try:
            df_copy = df.copy() 
            df_copy['datetime'] = pd.to_datetime(df_copy['datetime'])
            df_copy = df_copy.sort_values(by='datetime').reset_index(drop=True)
            df_copy['datetime'] = df_copy['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            raise TypeError(f"Could not convert 'datetime' column to datetime objects. Error: {e}")

        # Return the formatted dictionary payload
        return {
            "datetime": df_copy['datetime'].tolist(),
            "open": df_copy['open'].tolist(),
            "high": df_copy['high'].tolist(),
            "low": df_copy['low'].tolist(),
            "close": df_copy['close'].tolist(),
            "interval": interval,
            "interval_unit": interval_unit,
            "reasoning_mode": reasoning_mode
        }

    @staticmethod
    def _univariate_dict(df: pd.DataFrame, interval: int, interval_unit: str, reasoning_mode: str) -> dict:
       
        # Validate input DataFrame type
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input 'df' must be a pandas DataFrame.")

        # Check for required columns
        required_columns = ['datetime', 'value']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            raise KeyError(f"DataFrame is missing required columns: {missing_cols}")
        
        # Ensure 'datetime' column is of datetime type
        try:
            df_copy = df.copy() 
            df_copy['datetime'] = pd.to_datetime(df_copy['datetime'])
            df_copy = df_copy.sort_values(by='datetime').reset_index(drop=True)
            df_copy['datetime'] = df_copy['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            raise TypeError(f"Could not convert 'datetime' column to datetime objects. Error: {e}")

        # Return the formatted dictionary payload
        return {
            "datetime": df_copy['datetime'].tolist(),
            "value": df_copy['value'].tolist(),
            "interval": interval,
            "interval_unit": interval_unit,
            "reasoning_mode": reasoning_mode
        }



    def ohlc_model(self, data_input: Union[str, pd.DataFrame], interval: int, interval_unit: str, reasoning_mode: str, output_file=None) -> pd.DataFrame:
      
        data = ohlc_dataframe(data_input)

        data_length = len(data)        

        if not (5000 <= data_length <= 10000):
            raise ValueError(f"Number of data periods must be between 5000 and 10000. Got: {data_length}")

        payload = self._time_series_dict(data,interval,interval_unit,reasoning_mode)
        response_dict = self.send_post_request(self.CAUSAL_OHLC_ENV, payload)
  
        result_df = dict_to_dataframe(response_dict, 'datetime')
        if output_file is not None:
            result_df.to_csv(f"{output_file}.csv",index=False)
            print(f"Outputs saved to {output_file}.csv")
        
        print(f"Last 5 rows...\n{result_df.tail(5)}")

        return result_df

    def ohlc_forecast(self, data_input: Union[str, pd.DataFrame], interval: int, interval_unit: str, reasoning_mode: str) -> pd.DataFrame:
          
        data = ohlc_dataframe(data_input)

        data_length = len(data)        

        if not (5000 <= data_length <= 10000):
            raise ValueError(f"Number of data periods must be between 5000 and 10000. Got: {data_length}")

        payload = self._time_series_dict(data,interval,interval_unit,reasoning_mode)
        response_dict = self.send_post_request(self.CAUSAL_OHLC, payload)
        
        print(response_dict)

        return response_dict

    def univariate_model(self, data_input: Union[str, pd.DataFrame], interval: int, interval_unit: str, reasoning_mode: str, output_file=None) -> pd.DataFrame:
          
        data = univariate_dataframe(data_input)

        data_length = len(data)        

        if not (5000 <= data_length <= 10000):
            raise ValueError(f"Number of data periods must be between 5000 and 10000. Got: {data_length}")

        payload = self._univariate_dict(data,interval,interval_unit,reasoning_mode)
        response_dict = self.send_post_request(self.CAUSAL_UNIV_ENV, payload)
        result_df = dict_to_dataframe(response_dict, 'datetime')
        if output_file is not None:
            result_df.to_csv(f"{output_file}.csv",index=False)
            print(f"Outputs saved to {output_file}.csv")
        
        print(f"Last 5 rows...\n{result_df.tail(5)}")

        return result_df

    def univariate_forecast(self, data_input: Union[str, pd.DataFrame], interval: int, interval_unit: str, reasoning_mode: str) -> pd.DataFrame:
          
        data = univariate_dataframe(data_input)

        data_length = len(data)        

        if not (5000 <= data_length <= 10000):
            raise ValueError(f"Number of data periods must be between 5000 and 10000. Got: {data_length}")

        payload = self._univariate_dict(data,interval,interval_unit,reasoning_mode)
        response_dict = self.send_post_request(self.CAUSAL_UNIV, payload)
        
        print(response_dict)

        return response_dict



    def ohlc_rolling_forecast(self, data_input: Union[str, pd.DataFrame], interval: int, interval_unit: str, reasoning_mode: str,output_file=None, window_size: int = 5001) -> pd.DataFrame:
        
        custom_stamp = datetime.now().date()

        data = ohlc_dataframe(data_input)
   
        for i in range(0, len(df) - window_size + 1, 1):
         
            try:
                window_df = data.iloc[i:i + window_size]

                payload = self._time_series_dict(window_df,interval,interval_unit,reasoning_mode)
        
                response_dict = self.send_post_request(self.CAUSAL_OHLC, payload)

                write_dict_entry_to_csv(response_dict, f'{custom_stamp}.csv', separator=' ')

            except Exception as e:
                print(f"Error processing rolling window for datetime {payload['datetime'][-1]}: {e}")

    def univariate_rolling_forecast(self, data_input: Union[str, pd.DataFrame], interval: int, interval_unit: str, reasoning_mode: str,output_file=None, window_size: int = 5001) -> pd.DataFrame:
        
        custom_stamp = datetime.now().date()

        data = univariate_dataframe(data_input)

        for i in range(0, len(df) - window_size + 1, 1):
            
            try:
                window_df = data.iloc[i:i + window_size]

                payload = self._univariate_dict(window_df,interval,interval_unit,reasoning_mode)
        
                response_dict = self.send_post_request(self.CAUSAL_UNIV, payload)

                write_dict_entry_to_csv(response_dict, f'{custom_stamp}.csv', separator=' ')
                
            except Exception as e:
                print(f"Error processing rolling window for datetime {payload['datetime'][-1]}: {e}")


    def check_chain_propagation(current_tf, next_tf):

        current_tf['datetime'] = pd.to_datetime(current_tf['datetime'])
        next_tf['datetime'] = pd.to_datetime(next_tf['datetime'])

        non_zero_current = current_tf[current_tf['chain_detected'] != 0].copy()
        chain_change_mask = (non_zero_current['chain_detected'] != non_zero_current['chain_detected'].shift(1))
        tf_1 = non_zero_current[chain_change_mask]

        if tf_1.empty:
            raise ValueError("current dataframe is empty.")

        last_non_zero_row = tf_1.iloc[-1]
        chain_detected_value = last_non_zero_row['chain_detected']
        last_non_zero_datetime = last_non_zero_row['datetime']

        propagation_rules = next_tf[
            (next_tf['chain_detected'] != 0) &
            (next_tf['datetime'] >= last_non_zero_datetime) &
            (next_tf['chain_detected'] == chain_detected_value)
        ]

        if not propagation_rules.empty:

            tf_2 = propagation_rules.iloc[0]

            return (True,tf_2['datetime'], tf_2['chain_detected'])
        else:
            return (False, None, None)
