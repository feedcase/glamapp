from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.dao.base import BaseDAO
from src.media.models import MediaCategory, MediaUrl, MediaAccount


class MediaCategoryDAO(BaseDAO):
    model = MediaCategory

    @classmethod
    async def add_media_categories(cls, session: AsyncSession, category_names: list[str]):
        category_ids = []
        for category_name in category_names:
            category_name = category_name.lower().strip()
            stmt = select(cls.model).filter_by(category_name=category_name)
            result = await session.execute(stmt)
            category = result.scalars().first()

            if category:
                category_ids.append(category.id)
            else:
                category = cls.model(category_name=category_name)
                session.add(category)
                try:
                    await session.flush()
                    logger.info(f'Added category {category_name}')
                    category_ids.append(category.id)
                except SQLAlchemyError as e:
                    await session.rollback()
                    logger.error(f'Error while adding category {category_name}: {e}')
                    raise e

        return category_ids


class MediaAccountDAO(BaseDAO):
    model = MediaAccount

    @classmethod
    async def add_media_accounts(cls, session: AsyncSession, category_id: str | int, accounts_data: list[dict]):
        account_ids = []
        for account_data in accounts_data:
            account__username = account_data['username']

        return account_ids


class MediaUrlDAO(BaseDAO):
    model = MediaUrl

    @classmethod
    async def add_media_urls(cls, session: AsyncSession, category_id: str | int, urls: list[str]):
        media_url_ids = []
        for url in urls:
            url = str(url).strip()
            stmt = select(cls.model).filter_by(url=url, category_id=category_id)
            result = await session.execute(stmt)
            media_url = result.scalars().first()

            if media_url:
                media_url_ids.append(media_url.id)
            else:
                media_url = cls.model(url=url, category_id=category_id)
                session.add(media_url)
                try:
                    await session.flush()
                    logger.info(f'Added Media Url {url} for Category {category_id}')
                    media_url_ids.append(media_url.id)
                except SQLAlchemyError as e:
                    await session.rollback()
                    logger.error(f'Error while adding Media Url {url} for Category {category_id}: {e}')
                    raise e

        return media_url_ids
