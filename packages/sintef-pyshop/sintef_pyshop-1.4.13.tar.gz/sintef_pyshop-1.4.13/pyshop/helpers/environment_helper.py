import os
from typing import Union

deprecated_env_variables = ['ICC_COMMAND_PATH']
license_filename = 'SHOP_license.dat'

class EnvironmentHelper:
  @staticmethod
  def get_env_variable(environment_variable: Union[str, None]):
    if environment_variable in deprecated_env_variables:
      print(f"The environment variable '{environment_variable}' is deprecated in SHOP 16.0.0 and will be removed in the future. Use SHOP_BINARY_PATH and SHOP_LICENSE_PATH instead.")
    return os.getenv(environment_variable, None)
  
  @staticmethod
  def get_binary_path() -> str:
    binary_path = EnvironmentHelper.get_env_variable('SHOP_BINARY_PATH')
    
    if not binary_path:
      binary_path = EnvironmentHelper.get_env_variable('ICC_COMMAND_PATH')
      
    if not binary_path:
      raise Exception("No binary path found in environment variables. Please set SHOP_BINARY_PATH or solver_path argument in the ShopSession constructor.")
      
    return binary_path
  
  @staticmethod
  # @param license_path_argument the license path can be passed as an argument
  def get_license_path(license_path_argument: Union[str, None]) -> str:
    if license_path_argument:
      full_license_path = os.path.join(license_path_argument, license_filename)
      
      if not os.path.exists(full_license_path):
        raise Exception(f"SHOP_license.dat is not found in the path: {license_path_argument}")
      return license_path_argument
    
    shop_license_path = EnvironmentHelper.get_env_variable('SHOP_LICENSE_PATH')
    if shop_license_path:
      full_license_path = os.path.join(shop_license_path, license_filename)
      if not os.path.exists(full_license_path):
        raise Exception(f"SHOP_license.dat is not found in the path: {shop_license_path}")
      return shop_license_path

    icc_command_path = EnvironmentHelper.get_env_variable('ICC_COMMAND_PATH')
    if icc_command_path:
      full_license_path = os.path.join(icc_command_path, license_filename)
      if not os.path.exists(full_license_path):
        raise Exception(f"SHOP_license.dat is not found in the path: {icc_command_path}")
      return icc_command_path
    
    current_directory = os.getcwd()
    if os.path.exists(os.path.join(current_directory, license_filename)):
      return current_directory
    
    raise Exception("No license path found. Please set SHOP_LICENSE_PATH or by setting license_path argument in the ShopSession constructor.")
    
    