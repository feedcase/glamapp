from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    relationship,
    Mapped,
    mapped_column
)

from src.dao.database import (
    Base,
    str_uniq,
    str_null_true
)


class MediaCategory(Base):
    category_name: Mapped[str]

    def __str__(self):
        return (f'{self.__class__.__name__}(id={self.id}, '
                f'category_name={self.category_name!r})')

    def __repr__(self):
        return str(self)


class MediaAccount(Base):
    account_username: Mapped[str]
    category_id: Mapped[int] = mapped_column(ForeignKey('media_categories.id'), nullable=False)
    watermark: Mapped[str_null_true]

    category: Mapped['MediaCategory'] = relationship('MediaCategory', backref='media_accounts')

    def __str__(self):
        return (f'{self.__class__.__name__}(id={self.id}, '
                f'account_username={self.account_username!r}, '
                f'category={self.category!r})')

    def __repr__(self):
        return str(self)


class MediaUrl(Base):
    url: Mapped[str_uniq]
    category_id: Mapped[int] = mapped_column(ForeignKey('media_categories.id'), nullable=False)

    category: Mapped['MediaCategory'] = relationship('MediaCategory', backref='media_urls')

    def __str__(self):
        return (f'{self.__class__.__name__}(id={self.id}, '
                f'category={self.category!r},'
                f'url={self.url!r})')

    def __repr__(self):
        return str(self)
