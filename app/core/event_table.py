from sqlalchemy import event
from sqlalchemy.orm import ORMExecuteState ,with_loader_criteria, Session
from app.models.product import VisibilityMixin


@event.listens_for(Session, "do_orm_execute" ) 
def  _add_filtering_criteria ( execute_state: ORMExecuteState ): 
    if execute_state.is_select: 
        execute_state.statement = execute_state.statement.options( 
            with_loader_criteria( 
                VisibilityMixin, 
                lambda cls: cls.is_deleted.is_( False ), 
                include_aliases= True , 
            ) 
        )