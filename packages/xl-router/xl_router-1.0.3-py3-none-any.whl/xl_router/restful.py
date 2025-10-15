from typing import Optional
from pathlib import Path
import yaml
import inspect


class R:
    @classmethod
    def get_yaml_path(cls):
        caller_frame = inspect.stack()[2]
        caller_filepath = Path(caller_frame.filename)
        caller_dir = caller_filepath.parent
        return caller_dir / 'data.yaml'

    @classmethod
    def load_table_config(cls):
        yaml_path = cls.get_yaml_path()  
        table_config = {
            'columns': []
        }
        if yaml_path.exists():
            with yaml_path.open(encoding='utf-8') as f:
                table_config = yaml.safe_load(f)
        cls.params = [col['prop'] for col in table_config['columns']] 

    @classmethod
    def get(cls, 
            id: Optional[int] = None, 
            order_key: Optional[str] = 'id', 
            order_way: Optional[str] = 'desc',
            page_num: Optional[int] = None, 
            page_size: Optional[int] = None, 
            **kwargs):
        if id:
            return cls.get_json(id)
      
        else:
            order_by = {order_key: order_way} if order_key else {}
            params = getattr(cls, 'params', []) 
            kwargs = {key: kwargs[key] for key in kwargs if key in params }
            return cls.get_jsons(
                order_by=order_by, 
                page_num=page_num, 
                page_size=page_size,
                **kwargs
            )

    @classmethod
    def post(cls, data: dict):
        cls.add(data)

    @classmethod
    def put(cls, id: int, data: dict):
        cls.save(id, data)

    @classmethod
    def delete(cls, id: int):
        cls.delete_list(id=id)
