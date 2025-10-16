from django.db.models import PositiveIntegerField, Subquery


class SubqueryCount(Subquery):
    """
    from django.db.models import OuterRef

    weapons = Weapon.objects.filter(unit__player_id=OuterRef('id'))
    units = Unit.objects.filter(player_id=OuterRef('id'))

    qs = Player.objects.annotate(weapon_count=SubqueryCount(weapons),
                                rarity_sum=SubquerySum(units, 'rarity'))
    """

    # Custom Count function to just perform simple count on any queryset without grouping.
    # https://stackoverflow.com/a/47371514/1164966
    template = "(SELECT count(*) FROM (%(subquery)s) _count)"
    output_field = PositiveIntegerField()


class SubqueryAggregate(Subquery):
    # https://code.djangoproject.com/ticket/10060
    template = '(SELECT %(function)s(_agg."%(column)s") FROM (%(subquery)s) _agg)'

    def __init__(self, queryset, column, output_field=None, **extra):
        if not output_field:
            # infer output_field from field type
            output_field = queryset.model._meta.get_field(column)
        super().__init__(
            queryset, output_field, column=column, function=self.function, **extra
        )


class SubquerySum(SubqueryAggregate):
    function = "SUM"
