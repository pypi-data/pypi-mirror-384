from datetime import datetime
import hashlib
from sqlmodel import SQLModel
from typing import Tuple, Optional
from fastapi import HTTPException

from acex.core.models import DeviceConfig, StoredDeviceConfig



class DeviceConfigManager:
    """
    This class manages input and retreival of 
    device configurations. 
    """

    def __init__(self, db_manager):
        self.db = db_manager

    def list_config_hashes(
        self, 
        hostname: str,
        point_in_time: datetime = None,
        limit: int = 100,
        ) -> list: 

        session = next(self.db.get_session())
        try:
            # Bygg upp query med specifika kolumner (exkluderar content)
            query = session.query(
                StoredDeviceConfig.id,
                StoredDeviceConfig.hash,
                StoredDeviceConfig.created_at,
                StoredDeviceConfig.device_name
            ).filter(
                StoredDeviceConfig.device_name == hostname
            )
            
            if point_in_time is not None:
                query = query.filter(StoredDeviceConfig.created_at <= point_in_time)
                
            results = query.order_by(StoredDeviceConfig.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "id": result.id,
                    "hash": result.hash,
                    "created_at": result.created_at,
                    "device_name": result.device_name
                }
                for result in results
            ]
        finally:
            session.close()

    def get_config_by_hash(
        self,
        hostname:str,
        hash:str
        ) -> StoredDeviceConfig:

        session = next(self.db.get_session())
        try:
            existing = session.query(StoredDeviceConfig).filter(
                StoredDeviceConfig.hash == hash
            ).first()
            return existing
        finally:
            session.close()


    def get_latest_config(
        self,
        hostname:str,
        ) -> StoredDeviceConfig:
        print("LLL")

        session = next(self.db.get_session())
        try:
            existing = session.query(StoredDeviceConfig).filter(
                StoredDeviceConfig.device_name == hostname
            ).order_by(StoredDeviceConfig.created_at.desc()).first()
            return existing
        finally:
            session.close()


    def upload_config(
        self,
        config: DeviceConfig,
        ) -> StoredDeviceConfig: 
        # Use MD5 for widely adopted checksum (32 chars)
        # Fast and universally recognized for content verification
        config_hash = hashlib.md5(config.content.encode()).hexdigest()        

        # spara till db med hash
        session = next(self.db.get_session())
        try:
            # Kontrollera om ett objekt med samma hash redan finns
            existing_config = session.query(StoredDeviceConfig).filter(
                StoredDeviceConfig.device_name == config.device_name,
                StoredDeviceConfig.hash == config_hash
            ).first()
            
            if existing_config:
                # Kasta HTTPException med 409 Conflict när konfigurationen redan finns
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Config not changed since last time",
                        "last_hash": config_hash,
                        "last_change": str(existing_config.created_at),
                        "device_name": config.device_name
                    }
                )

            save_this = StoredDeviceConfig(
                device_name=config.device_name,
                hash=config_hash,
                content=config.content
            )
            
            # Lägg till objektet i sessionen och spara
            session.add(save_this)
            session.commit()
            session.refresh(save_this)  # Uppdatera objektet med det genererade ID:t
            
            return save_this
        finally:
            session.close()

