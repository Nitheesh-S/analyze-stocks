from pydantic import BaseModel


class ThirdPartyToken(BaseModel):
	id: int
	access_token: str
	refresh_token: str
	website: str

	class Config:
		orm_mode = True


class Stock(BaseModel):
	symbol: str
	exchange: str
	is_active: bool

	class Config:
		orm_mode = True