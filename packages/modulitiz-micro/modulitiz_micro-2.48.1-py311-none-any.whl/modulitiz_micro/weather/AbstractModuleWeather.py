import json
from abc import ABC

from modulitiz_micro.exceptions.http.ExceptionHttpGeneric import ExceptionHttpGeneric
from modulitiz_micro.rete.http.ModuloHttp import ModuloHttp
from modulitiz_micro.rete.http.ModuloHttpUtils import ModuloHttpUtils
from modulitiz_micro.weather.beans.current.WeatherCurrentDataBean import WeatherCurrentDataBean
from modulitiz_micro.weather.beans.forecast.WeatherForecastDataBean import WeatherForecastDataBean
from modulitiz_nano.files.ModuloLogging import ModuloLogging


class AbstractModuleWeather(ABC):
	OPTIONS="lang=it&units=metric"
	KEY="appid=e28cd365c35c12e3ed8f2d84e04398c9"
	
	__BASE_URL="https://api.openweathermap.org"
	URL_CURRENT=__BASE_URL+f"/data/2.5/weather?{OPTIONS}&{KEY}&q="
	URL_FORECAST=__BASE_URL+f"/data/2.5/forecast?{OPTIONS}&{KEY}&q="
	
	def __init__(self,logger:ModuloLogging):
		self._logger=logger
	
	def getCurrent(self,city:str,codState:str)-> WeatherCurrentDataBean:
		return WeatherCurrentDataBean(self.__makeGenericRequest(self.URL_CURRENT, city,codState))
	
	def getForecast(self,city:str,codState:str)->WeatherForecastDataBean:
		return WeatherForecastDataBean(self.__makeGenericRequest(self.URL_FORECAST,city,codState))
	
	def __makeGenericRequest(self,baseUrl:str,city:str,codState:str)-> dict|None:
		url=baseUrl+ModuloHttpUtils.encodeUrl(city+","+codState)
		http=ModuloHttp(url,self._logger,False)
		try:
			response=http.doGet(0,False)
		except ExceptionHttpGeneric:
			return None
		return json.loads(response.responseBody)
