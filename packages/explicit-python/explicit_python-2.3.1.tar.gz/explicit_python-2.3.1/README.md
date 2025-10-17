# Explicit
## Набор компонентов для построения явной (Explicit) многослойной архитектуры

[<img alt="explicit architecture" src="doc/100-explicit-architecture-svg.png" width=700>][explicit architecture]

## Решаемые проблемы
- Образование [BBoM] в приложении
- Смешивание [бизнес-логики][domain-model], [логики выборки данных][service-layer], запросов UI
- [Зацепление][coupling] модулей приложения
- [Дублирование логики][dry]

## Основные принципы построения
- [CQRS]:
  - Поток команд (Command), модифицирующий состояние приложения (БД) идёт через [слой предметной области][domain-model]
  - Поток запросов (Query) не меняет состояние и не проходит через предметную область
- В основе лежит [Явная архитектура][explicit architecture]: слой предметной области не зависит от сервисного слоя или конкретных реализаций ORM, СУБД, API сторонних служб и т.д.; используются порты и адаптеры абстрагируют вызовы к API; ядро приложения отделено от взаимодействующих с ним API, GUI, webservices.

## Реализуемые компоненты
### Команда (command)
Инкапсулирует передачу параметров запроса обработчику команды, стандартизирует передачу параметров:

```python
  # Application core
  class RegisterStudent(Command):
    last_name: str
    first_name: str
```

### Обработчик команды (command handler)
Принимает команду и выполняет действия над переданными в команде данными.
```python
  # Application core
  def register_student(command: RegisterStudent):  # handler
      student = Student(last_name=command.last_name, first_name=command.first_name)
      repository.add(student)
```

### Шина (bus, messagebus)
Обеспечивает доставку команды соответствующему обработчику, уменьшает зацепление между модулями и слоями приложения.
```python
  from core import bus

  # Django Rest Framework
  class StudentViewSet(ModelViewSet):
  
    def perform_create(self, serializer):
        command = RegisterStudent(**serializer.validated_data)
        bus.handle(command)
    
  # Spyne webservices
  @rpc(
    StudentData,
  )
  def RegisterStudent(ctx, data: 'StudentData'):
    command = RegisterStudent(last_name=data.last_name, first_name=data.first_name)
    bus.handle(command)
  
```

### Unit of Work

[Unit of Work]:
- Единица работы, логическая бизнес-транзация
- Обеспечивает атомарность выполняемых операций
- Предоставляет доступ к репозиториям приложения
- Устраняет зависимость логики от конкретного фреймворка или технологии БД

```python
def register_student(command: RegisterStudent, uow: 'UnitOfWork'):
    with uow.wrap():
        uow.users.add(user)
        uow.persons.add(person)
        uow.students.add(student)
```

### Репозиторий (Repository)
[Repository]:
- Является адаптером к СУБД
- Выполняет роль хранилища объектов предметной области в соответствующем слое
- Инкапсулирует логику выборки данных
- Устраняет зависимость логики от конкретного фреймворка или технологии БД

```python
class Repository:
    def get_object_by_id(self, identifier: int) -> Student:
        try:
            dbinstance = DBStudent.objects.get(pk=identifier)
            return self._to_domain(dbinstance)
        except ObjectDoesNotExist as e:
            raise StudentNotFound() from e

    def get_by_persons(self, *persons: 'Person') -> Generator[Student, None, None]:
        query = DBStudent.objects.filter(person_id__in=(person.id for person in persons))
        for dbinstance in query.iterator():
            yield self._to_domain(dbinstance)
```

### Фабрика (Factory)
Инкапсулирует логику создания нового объекта предметной области по известным параметрам.
```python
class Factory(AbstractDomainFactory):
    def create(self, data: StudentDTO) -> Student:
        return Student(
            person_id=data.person.id,
            unit_id=data.unit.id,
        )
```

### Объект передачи данных (DTO, Data Transfer Object)
[DTO] используется при передаче большого количества параметров между объектами приложения и для стандартизации передачи данных и контрактов.

```python

def create_person(data: 'PersonDTO'):
    person = factory.create(data)

def update_person(person, data: 'PersonDTO'):
    domain.update_person(data)

```

## Обработка входящего запроса и события

### 1. Обработка запроса

   1.1 Запрос приходит в контроллер (View, Spyne @rpc и т.д.)

   1.2 Контроллер извлекает параметры запроса, валидирует их, формирует команду с параметрами запроса

   1.3 Сформированная команда направляется в шину ядра приложения

   ```python
   def post(self, request, *args, **kwargs):
     serializer = self.get_serializer(data=request.data)
     serializer.is_valid(raise_exception=True)
     last_name = serializer.validated_data['last_name']
     first_name = serializer.validated_data['first_name']
   
     command = RegisterStudent(
         last_name=last_name,
         first_name=first_name,
     )
     bus.handle(command)
     return JsonResponse(data={'registered': True})
   ```

   1.4 Шина по типу команды определяет соответствующий обработчик и передает ему команду

   ```python
   class CommandBusMixin(ABC):
   
      _command_handlers: Dict[Type[Command], Callable] = {}
      
      def handle_command(self, command: Command):
         """Передача запроса обработчику типа данного запроса."""
         return self._command_handlers[type(command)](command)
   ```

   1.5 Обработчик выполняет требуемые действия, инициирует событие, соответствующее результату обработки, возвращает результат
 
   ```python
   def register_student(
      command: RegisterStudent, uow: 'UnitOfWork'
   ) -> 'Student':
      with uow.wrap():
          student: Student = domain_register_student(
              StudentDTO(**command.dict())
          )
      uow.add_event(events.StudentCreated(
          **command.dict(), **asdict(student)
      ))
      return student
   ```

   1.6 Событие попадает в шину ядра

   1.7 Ядро определяет список обработчиков, соответствующих типу события, передает им инстанс события

   ```python
   class EventBusMixin(ABC):
   
      _event_handlers: Dict[Type[Event], List[EventHandler]] = {}
   
      def handle_event(self, event: Event):
          """Передача события списку обработчиков типа данного события."""
          consume(
              handler(event)
              for handler in self._event_handlers[type(event)]
          )
   ```

   1.8 Обработчик события выполняет требуемые действия

   1.9 Обработчик события может передать событие на внешнюю шину, воспользовавшись соответствующим адаптером шины

   ```python
   def on_student_created(
      event: events.StudentCreated, adapter: 'AbstractAdapter'
   ):
      adapter.publish(
          'edu.students.created',
          json.dumps(asdict(event), default=encoder)
      )
   ```

### 2. Обработка внешнего события

   2.1 Подписчик получает событие из внешней шины

   2.2 Подписчик десериализует внешнее событие и инстанцирует внутреннее

   ```python
   def bootstrap():
      from students.core.adapters.messaging import adapter
      from students.core.domain import events
      
      TOPIC_EVENTS = {
         'edu.persons.created': events.PersonCreated,
      }
      
      for message in adapter.subscribe(*TOPIC_EVENTS):
         event = TOPIC_EVENTS[message.topic()](
             **json.loads(message.value())
         )
         bus.handle(event)

   ```

   2.3 Внутренее событие попадает в шину ядра

   2.4 Ядро определяет список обработчиков, соответствующих типу события, передает им инстанс события

   2.5 Обработчик события выполняет требуемые действия

   2.6 Обработчик события может инстанцировать новое событие

   ```python
   def on_person_created(
      event: events.PersonCreated, uow: 'UnitOfWork'
   ) -> None:
      with uow.wrap():
          transaction_id = event.meta.transaction_id
   
          saga = uow.sagas.get_object_by_uuid(transaction_id)
          student = uow.students.get_object_by_id(saga.student_id)
   
          student.person_id = event.id
          uow.students.update(student)
   
          uow.add_event(events.StudentCreated(
              **command.dict(), **asdict(student)
          ))
   ```


## Минимальный пример реализации
Можно увидеть в тестовом приложении src/testapp.

## Запуск тестов
```sh
$ tox
```


[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)

   [bbom]: <https://ru.wikipedia.org/wiki/Большой_комок_грязи>
   [ddd]: <https://ru.wikipedia.org/wiki/Предметно-ориентированное_проектирование>
   [domain-model]: <http://design-pattern.ru/patterns/domain-model.html>
   [service-layer]: <http://design-pattern.ru/patterns/service-layer.html>
   [coupling]: <https://ru.wikipedia.org/wiki/Зацепление_(программирование)>
   [dry]: <https://ru.wikipedia.org/wiki/Don’t_repeat_yourself>
   [cqrs]: <https://martinfowler.com/bliki/CQRS.html>
   [explicit architecture]: <https://herbertograca.com/2017/11/16/explicit-architecture-01-ddd-hexagonal-onion-clean-cqrs-how-i-put-it-all-together/>
   [unit of work]: <http://design-pattern.ru/patterns/unit-of-work.html>
   [repository]: <http://design-pattern.ru/patterns/repository.html>
   [dto]: <http://design-pattern.ru/patterns/data-transfer-object.html>
