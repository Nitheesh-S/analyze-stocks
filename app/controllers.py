from . import models
from sqlalchemy.orm import Session


def get_last_updated_date(symbol_master_id: int, db: Session):
	last_row = (
        db.query(models.SymbolHistory)
        .filter_by(symbol_master_id=symbol_master_id)
        .order_by(models.SymbolHistory.id.desc())
		.first()
    )
	if not last_row:
		return None
	return last_row.timestamp