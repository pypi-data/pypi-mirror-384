from django.db.models import Manager, QuerySet


class AccountManager:
    class AccountManager(Manager):
        def get_queryset(self) -> QuerySet:
            return AccountManager.AccountQuerySet(self.model, using=self._db).filter()

    class AccountQuerySet(QuerySet):
        def suggest(self, account, *args, **kwargs):
            return self.exclude(id=account.id).filter(*args, **kwargs)
