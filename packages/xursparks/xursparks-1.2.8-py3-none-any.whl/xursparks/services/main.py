from xursparks.error.main import GenericXursparksException as gxe
import requests, configparser

class XursparksService:
    def __init__(self) -> None:
        pass

    def fetch(self,
              api_url:str = None,
              api_key:str = None,
              api_secret: str = None,
              type: str = None) -> dict:
        resp:dict

        if api_url is None:
            return gxe(f'api_url is None')

        headerToken = f'Token {api_key}:{api_secret}'
        resp = requests.get(api_url, headers={'Authorization': headerToken})

        if type is not None and type.strip().lower() == 'json':
            resp = resp.json()

        return resp
    
    def loadPropertiesFile(self,
                           properties_path:str) -> any:
        if properties_path is None:
            return gxe(f'properties_path is None')
        properties:any
        properties = configparser.ConfigParser()
        properties.read(properties_path)

        return properties
    
    def getPropertyFromFile(self,
                           properties_path:str,
                           property_key:str,
                           property_group:str = None) -> str:
        if properties_path is None:
            return gxe(f'properties_path is None')
        
        if property_key is None:
            return gxe(f'property_key is None')
        
        if property_group is None:
            property_group = "default"
        
        property_value:str
        properties = configparser.ConfigParser()
        properties.read(properties_path)
        property_value = properties.get(property_group, property_key)

        return property_value