from modulitiz_micro.weather.AbstractModuleWeather import AbstractModuleWeather


class ModuleWeather(AbstractModuleWeather):
	"""
	Utility for current weather and forecasts.
	https://openweathermap.org/api
	"""
	
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
