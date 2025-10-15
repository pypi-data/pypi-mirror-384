from django.conf import (
    settings,
)
from django.core.management import (
    BaseCommand,
)

from edu_rdm_integration.rdm_models.models import (
    RDMModelEnum,
)
from edu_rdm_integration.stages.service.model_outdated_data.managers import (
    ModelOutdatedDataCleanerManager,
)


class Command(BaseCommand):
    """Ночная команда для очистки устаревших данных РВД."""

    nightly_script = True

    help = 'Ночная команда для очистки устаревших данных РВД.'

    def add_arguments(self, parser):
        """Добавляет аргументы командной строки."""
        models = ', '.join(f'{key} - {value.title}' for key, value in RDMModelEnum.get_enum_data().items())
        models_help_text = (
            f'Значением параметра является перечисление моделей РВД, для которых должна быть произведена зачистка '
            f'устаревших данных. '
            f'Перечисление моделей:\n{models}. Если модели не указываются, то зачистка устаревших данных будет '
            f'производиться для всех моделей. Модели перечисляются через запятую без пробелов.'
        )
        parser.add_argument(
            '--models',
            action='store',
            dest='models',
            type=lambda ml: [m.strip().upper() for m in ml.strip().split(',')] if ml else None,
            help=models_help_text,
        )

        parser.add_argument(
            '--safe',
            action='store_true',
            dest='safe',
            default=False,
            help='Запускать команду в безопасном режиме (без удаления данных, только логирование).',
        )

        parser.add_argument(
            '--log-sql',
            action='store_true',
            dest='log_sql',
            default=False,
            help='Включить логирование SQL-запросов, выполняемых во время работы команды.',
        )

    def _cleanup_model_outdated_data(self, options):
        """Очистка устаревших данных моделей РВД."""
        model_data_cleaner_manager = ModelOutdatedDataCleanerManager(
            models=options['models'],
            safe=options['safe'],
            log_sql=options['log_sql'],
        )
        model_data_cleaner_manager.run()

    def handle(self, *args, **options):
        """Запуск очистки устаревших данных РВД."""
        if settings.RDM_ENABLE_CLEANUP_MODELS_OUTDATED_DATA:
            self._cleanup_model_outdated_data(options)
