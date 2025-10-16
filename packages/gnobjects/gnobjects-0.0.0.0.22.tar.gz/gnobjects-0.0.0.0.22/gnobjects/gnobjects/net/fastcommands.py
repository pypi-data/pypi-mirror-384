from typing import Optional, Union, List

from KeyisBTools.models.serialization import SerializableType

from .objects import GNResponse, FileObject, CORSObject



class GNFastCommand(GNResponse):
    """
    # Быстрый ответ
    """
    def __init__(self,
                 payload: Optional[SerializableType] = None,
                 files: Optional[Union[str, FileObject, List[FileObject]]] = None,
                 cors: Optional[CORSObject] = None):

        command = getattr(self, "cls_command", None)
        if command is None:
            command = 'gn:client:undefined'

        super().__init__(command=command, payload=payload, files=files, cors=cors)



class AllGNFastCommands:
    class ok(GNFastCommand):
        """
        # Корректный ответ
        """
        cls_command = True
       
        
    class UnprocessableEntity(GNFastCommand):
        """
        # Некорректные данные
        Ошибка указывает, что сервер понял запрос, но не может его обработать из-за неверного содержания. 
        Пример: передан payload с правильной структурой, но поля содержат некорректные значения (например, строка вместо числа).
        Используется, когда данные формально корректны, но нарушают бизнес-логику.
        """
        cls_command = "gn:origin:422"


    class BadRequest(GNFastCommand):
        """
        # Неправильный синтаксис url или параметров
        Сервер не может понять запрос из-за ошибок в структуре или параметрах. 
        Пример: отсутствует обязательный параметр или указан некорректный формат даты.
        Часто используется при валидации входных данных на уровне запроса.
        """
        cls_command = "gn:origin:400"


    class Forbidden(GNFastCommand):
        """
        # Доступ запрещён, даже при наличии авторизации
        Клиент аутентифицирован, но не имеет прав для выполнения действия. 
        Пример: пользователь вошёл в систему, но пытается изменить чужие данные.
        Используется для разграничения прав доступа.
        """
        cls_command = "gn:origin:403"


    class Unauthorized(GNFastCommand):
        """
        # Требуется авторизация
        Ошибка возвращается, если запрос требует входа, но клиент не предоставил или предоставил неверные данные авторизации. 
        Пример: отсутствует заголовок Authorization или токен недействителен.
        Используется для защиты закрытых API-эндпоинтов.
        """
        cls_command = "gn:origin:401"


    class NotFound(GNFastCommand):
        """
        # Ресурс не найден
        Запрошенный объект или путь не существует на сервере. 
        Пример: попытка получить пользователя с несуществующим ID.
        Часто используется для API-ответов на невалидные ссылки.
        """
        cls_command = "gn:origin:404"


    class MethodNotAllowed(GNFastCommand):
        """
        # Метод запроса не поддерживается данным ресурсом
        Ресурс существует, но используемый gn-метод недопустим. 
        Пример: к ресурсу разрешён только GET, а клиент делает POST.
        Используется для ограничения набора действий над конкретными ресурсами.
        """
        cls_command = "gn:origin:405"


    class Conflict(GNFastCommand):
        """
        # Конфликт состояния ресурса (например, дубликат)
        Возникает, когда операция не может быть выполнена из-за противоречия с текущим состоянием ресурса. 
        Пример: попытка зарегистрировать пользователя с уже существующим email.
        Используется для предотвращения логических коллизий.
        """
        cls_command = "gn:origin:409"


    class InternalServerError(GNFastCommand):
        """
        # Внутренняя ошибка сервера
        Сервер столкнулся с непредвиденной ситуацией, которая не позволяет выполнить запрос. 
        Пример: необработанное исключение в коде приложения.
        Используется как универсальная ошибка для внутренних сбоев.
        """
        cls_command = "gn:origin:500"


    class NotImplemented(GNFastCommand):
        """
        # Метод или функционал ещё не реализован
        Сервер распознаёт запрос, но не поддерживает требуемый функционал. 
        Пример: метод API описан в документации, но ещё не реализован.
        Используется для обозначения незавершённых частей системы.
        """
        cls_command = "gn:origin:501"


    class ServiceUnavailable(GNFastCommand):
        """
        # Сервис временно недоступен
        Сервер не может обработать запрос из-за перегрузки или обслуживания. 
        Пример: база данных недоступна или сервис в режиме обновления.
        Используется для сигнализации о временных проблемах.
        """
        cls_command = "gn:origin:503"


    class GatewayTimeout(GNFastCommand):
        """
        # Таймаут при обращении к апстриму
        Прокси или шлюз не дождался ответа от вышестоящего сервера в установленный срок. 
        Пример: запрос к медленному backend-сервису превысил лимит времени.
        Используется для контроля SLA и таймаутов в распределённых системах.
        """
        cls_command = "gn:origin:504"
# dns

    class DnsDomainAccessDenied(GNFastCommand):
        """
        # DNS Доступ к домену запрещён
        Запрос был отклонён из-за настроек доступа.
        """
        cls_command = "gn:dns:601"


    class DnsInvalidVerificationAlgorithm(GNFastCommand):
        """
        # DNS Некорректный алгоритм подписи
        Сервер указал неподдерживаемый или неверный алгоритм подписи при проверке доступа к домену.
        """
        cls_command = "gn:dns:602"


    class DnsServerKeyNotFound(GNFastCommand):
        """
        # DNS Не удалось получить ключ сервера
        При попытке разрешить домен отсутствует ключ сервера для верификации подписи.
        Пример: запись в реестре доменов повреждена или отсутствует.
        """
        cls_command = "gn:dns:603"


    class DnsInvalidSignature(GNFastCommand):
        """
        # DNS Некорректная подпись
        Полученная подпись при попытке разрешить домен не прошла криптографическую проверку.
        Пример: данные были подменены в процессе передачи.
        """
        cls_command = "gn:dns:604"


    class DnsDomainDecryptionError(GNFastCommand):
        """
        # DNS Ошибка при расшифровке запроса
        Во время обработки запроса для разрешения домена произошла ошибка при расшифровке.
        Пример: клиент использовал неверный ключ или формат данных.
        """
        cls_command = "gn:dns:605"


    class DnsDomainNotFound(GNFastCommand):
        """
        # DNS Запрашиваемый домен не найден
        Домен отсутствует в системе или не имеет действующих записей.
        Пример: опечатка в имени или удалённая зона.
        """
        cls_command = "gn:dns:606"


    class DnsSenderDomainMismatch(GNFastCommand):
        """
        # DNS Несоответствие домена отправителя
        Проверка показала, что указанный отправитель не соответствует ожидаемому домену.
        Пример: подмена адреса в заголовках.
        """
        cls_command = "gn:dns:607"


    class DnsDomainResolutionDenied(GNFastCommand):
        """
        # DNS Не удалось получить доступ к разрешению домена
        Процесс разрешения домена был отклонён системой.
        """
        cls_command = "gn:dns:608"

# cors
    class CorsOriginNotAllowed(GNFastCommand):
        """
        # CORS Запрещённый источник
        Источник запроса (Origin) не разрешён в списке `allow_origins`.
        Пример: запрос с домена, который отсутствует в политике безопасности.
        """
        cls_command = "gn:cors:701"


    class CorsMethodNotAllowed(GNFastCommand):
        """
        # CORS Запрещённый метод
        Метод запроса не разрешён в списке `allow_methods`.
        Пример: попытка выполнить `delete` при разрешённых только `get` и `post`.
        """
        cls_command = "gn:cors:702"


    class CorsClientTypeNotAllowed(GNFastCommand):
        """
        # CORS Запрещённый тип клиента
        Тип клиента отсутствует в списке `allow_client_types`.
        Пример: доступ разрешён только 'proxy' и 'server', но запрос пришёл от 'client'.
        """
        cls_command = "gn:cors:703"


    class CorsTransportProtocolNotAllowed(GNFastCommand):
        """
        # CORS Запрещённый транспортный протокол
        Используемый транспортный протокол не разрешён в списке `allow_transport_protocols`.
        Пример: попытка доступа через gn:quik:dev при разрешённом только gn:quik:real.
        """
        cls_command = "gn:cors:704"


    class CorsRouteProtocolNotAllowed(GNFastCommand):
        """
        # CORS Запрещённый маршрутный протокол
        Указанный маршрутный протокол не разрешён в списке `allow_route_protocols`.
        Пример: запрос с использованием нестандартного маршрута.
        """
        cls_command = "gn:cors:705"


    class CorsRequestProtocolNotAllowed(GNFastCommand):
        """
        # CORS Запрещённый протокол запроса
        Протокол, указанный в запросе, не разрешён в списке `allow_request_protocols`.
        Пример: запрос с использованием нестандартного протокола.
        """
        cls_command = "gn:cors:706"

# kdc
    class KDCDecryptRequestFailed(GNFastCommand):
        """
        # KDC Ошибка расшифровки запроса
        Не удалось расшифровать входящий запрос.  
        Пример: переданный клиентом зашифрованный блок не совпадает с ожидаемым форматом или ключами.
        """
        cls_command = "gn:kdc:891"


    class KDCDecryptResponseFailed(GNFastCommand):
        """
        # KDC Ошибка расшифровки ответа
        Не удалось расшифровать ответ сервера.  
        Пример: клиент не смог корректно расшифровать данные, возвращённые сервером.
        """
        cls_command = "gn:kdc:892"


    class KDCSignatureVerificationFailed(GNFastCommand):
        """
        # KDC Ошибка проверки подписи
        Подпись запроса или ответа не прошла валидацию.  
        Пример: данные были изменены или использован неверный ключ.
        """
        cls_command = "gn:kdc:893"


    class KDCDomainVerificationFailed(GNFastCommand):
        """
        # KDC Ошибка проверки домена
        Не удалось подтвердить указанный домен.
        """
        cls_command = "gn:kdc:894"


    class KDCInvalidRequestFormat(GNFastCommand):
        """
        # KDC Некорректный формат запроса
        Запрос имеет недопустимый или повреждённый формат.
        """
        cls_command = "gn:kdc:895"


    class KDCInvalidResponseFormat(GNFastCommand):
        """
        # KDC Некорректный формат ответа
        Ответ имеет недопустимый или повреждённый формат.  
        Пример: сервер вернул некорректный блок сессионных данных.
        """
        cls_command = "gn:kdc:896"


    class KDCServerSessionKeyMissing(GNFastCommand):
        """
        # KDC Ошибка получения сессионных ключей
        Не удалось получить сессионные ключи сервера.
        """
        cls_command = "gn:kdc:897"


    class KDCServerSessionKeySignatureFailed(GNFastCommand):
        """
        # KDC Ошибка подписи сессионных ключей
        Подпись при получении сессионных ключей сервера не прошла валидацию. 
        """
        cls_command = "gn:kdc:898"



globals().update({
    name: obj
    for name, obj in AllGNFastCommands.__dict__.items()
    if isinstance(obj, type) and issubclass(obj, GNFastCommand)
})







