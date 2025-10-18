from dataclasses import dataclass


@dataclass
class WeatherBean:
	id: int
	main: str
	description: str
	icon: str
