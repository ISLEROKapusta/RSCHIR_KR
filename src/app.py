
from fastapi import FastAPI, Query, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, result_tuple, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError
import os

# Настройка базы данных
DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('MYSQL_USER', 'user')}:"
    f"{os.getenv('MYSQL_PASSWORD', 'password')}@"
    f"{os.getenv('MYSQL_HOST', 'app_mysql')}/"
    f"{os.getenv('MYSQL_DATABASE', 'appDB')}?charset=utf8mb4"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Модель базы данных для статусов посылок
class ParcelStatus(Base):
    __tablename__ = "parcel_statuses"
    id_state = Column(Integer, primary_key=True, index=True)
    status_name = Column(String(50), nullable=False)

# Модель базы данных для посылок
class Parcel(Base):
    __tablename__ = "parcels"
    id_parcels = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(50), unique=True, nullable=False)
    current_status = Column(Integer, ForeignKey("parcel_statuses.id_state"), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Установка значения по умолчанию и обновления
    cargo = Column(String(255))

    # Отношение для получения статуса
    status = relationship("ParcelStatus", backref="parcels")

app = FastAPI()

# HTML-шаблон
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Просмотр посылок</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background-color: #f4f4f9;
        }}
        h1 {{
            color: #333;
        }}
        form {{
            display: inline-block;
            text-align: left;
            margin-top: 30px;
            padding: 20px;
            background-color: #fff;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            width: 80%;
        }}
        label {{
            font-size: 16px;
            margin-bottom: 10px;
            margin-top: 20px;
        }}
        input {{
            width: 100%;
            padding: 8px;
            margin: 8px 0;
            border-radius: 5px;
            border: 1px solid #ccc;
        }}
        button {{
            margin-top: 20px; 
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
        button:hover {{
            background-color: #45a049;
        }}
        table {{
            width: 80%;
            margin: 20px auto;
            border-collapse: collapse;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>
    <h1>Просмотр посылок</h1>
    <form method="get" action="/view_parcels">
        <label for="start_id">ID начала:</label>
        <input type="number" id="start_id" name="start_id" min="1" value="1">
        <label for="end_id">ID конца:</label>
        <input type="number" id="end_id" name="end_id" min="1" value="10">
        <button type="submit">Показать</button>
    </form>
    <form method="post" action="/update_parcels">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Трек. номер</th>
                    <th>Статус</th>
                    <th>Обновлено</th>
                    <th>Груз</th>
                    <th style="text-align: center;">🗑</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        <button type="submit">Подтвердить изменения</button>
    </form>
    <div class="back-button">
        <button onclick="window.location.href='/'">Вернуться на главную</button>
    </div>
    <div class="back-button">
       <button type="button" onclick="window.location.href='/reindex_parcels'">Реиндексировать</button>
    </div>
</body>
</html>
"""

@app.get("/")
async def root():
    return FileResponse("index.html")

start_id_gl: int = 5
end_id_gl: int = 10

@app.get("/view_parcels")
async def view_parcels(start_id: int = Query(5), end_id: int = Query(10)):
    session = SessionLocal()
    global start_id_gl
    start_id_gl = start_id
    global end_id_gl
    end_id_gl=end_id

    #start_id=start_id_gl
    #end_id=end_id_gl
    try:
        parcels = (
            session.query(Parcel)
            .filter(Parcel.id_parcels.between(start_id, end_id))
            .order_by(Parcel.id_parcels)
            .all()
        )
        # Статусы для выпадающего списка
        statuses = session.query(ParcelStatus).all()
        status_options = {status.id_state: status.status_name for status in statuses}

        rows = "".join(
            f"<tr><td>{parcel.id_parcels}</td>"
            f"<td>{parcel.tracking_number}</td>"
            f"<td><select name='status_{parcel.id_parcels}'>"
            + "".join(
                f"<option value='{status_id}' {'selected' if parcel.current_status == status_id else ''}>"
                f"{status_name}</option>"
                for status_id, status_name in status_options.items()
            )
            + "</select></td>"
              f"<td>{parcel.updated_at}</td>"
              f"<td>{parcel.cargo or ''}</td>"
              f"<td><input type='checkbox' name='delete_{parcel.id_parcels}' value='1'></td></tr>"
            for parcel in parcels
        )

        return HTMLResponse(HTML_TEMPLATE.format(rows=rows))
    except SQLAlchemyError as e:
        return HTMLResponse(HTML_TEMPLATE.format(rows=f"<tr><td colspan='5'>Ошибка: {e}</td></tr>"))
    finally:
        session.close()


@app.post("/update_parcels")
async def update_parcels(request: Request, start_id: int = Query(1), end_id: int = Query(10)):
    session = SessionLocal()
    start_id = start_id_gl
    end_id = end_id_gl
    try:
        # Получаем данные из формы
        form = await request.form()

        # Обновляем статусы
        for parcel in session.query(Parcel).filter(Parcel.id_parcels.between(start_id, end_id)).all():
            # Обновление статуса
            status_id = int(form.get(f"status_{parcel.id_parcels}"))
            parcel.current_status = status_id

            # Проверка, нужно ли удалить эту посылку
            if form.get(f"delete_{parcel.id_parcels}") == '1':
                session.delete(parcel)

        # Сохраняем изменения
        session.commit()

        # Возврат HTML с уведомлением
        notification_script = """
        <script>
            alert('Статусы успешно обновлены и удалены');
            window.location.href = '/view_parcels?start_id={start_id}&end_id={end_id}';
        </script>
        """.format(start_id=start_id, end_id=end_id)

        return HTMLResponse(notification_script)
    except SQLAlchemyError as e:
        session.rollback()
        return {"error": str(e)}
    finally:
        session.close()

@app.get("/reindex_parcels")
async def reindex_parcels():
    session = SessionLocal()
    try:
        # Получаем все посылки
        parcels = session.query(Parcel).all()

        # Начинаем с ID = 1
        for idx, parcel in enumerate(parcels, start=1):
            parcel.id_parcels = idx  # Устанавливаем новый ID
        session.commit()

        # Возвращаем пользователю уведомление о завершении реиндексации
        notification_script = """
        <script>
            alert('Посылки успешно реиндексированы');
            window.location.href = '/view_parcels?start_id=1&end_id=10';
        </script>
        """
        return HTMLResponse(notification_script)

    except SQLAlchemyError as e:
        session.rollback()
        return {"error": str(e)}
    finally:
        session.close()

#####################################################################

html_content = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Добавить новый элемент</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background-color: #f4f4f9;
        }
        h1 {
            color: #333;
        }
        form {
            display: inline-block;
            width: 60%;
            text-align: left;
            margin-top: 30px;
            padding: 20px;
            background-color: #fff;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        label {
            font-size: 16px;
            margin-bottom: 10px;
            margin-top: 20px;
            display: block;
        }
        input, select {
            width: 90%;
            padding: 8px;
            margin: 8px 0;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        button {
            margin-top:10px;
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        .back-button {
            margin-top: 20px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <h1>Добавить новый элемент в таблицу посылок</h1>
    <form action="/page_add_new" method="POST">
        <label for="status">Статусы:</label>
        {statuses} 
        <label for="cargo">Груз:</label>
        <input type="text" id="cargo" name="cargo" placeholder="Введите описание груза">
        <button type="submit">Добавить</button>
    </form>
    
    <div class="back-button">
        <button onclick="window.location.href='/'">Вернуться на главную</button>
    </div>
</body>
</html>
"""


# FastAPI endpoint для получения формы с динамическими статусами
@app.get("/page_add_new")
async def add_parcel_form():
    session = SessionLocal()
    statuses = session.query(ParcelStatus).all()
    session.close()

    # Форматируем статусные опции для вставки в HTML
    status_options = f"<select id='status' name='status'>" + "".join(
        f"<option value='{status.id_state}'>{status.status_name}</option>" for status in statuses
    ) + "</select>"
    result=html_content.split("{statuses}")[0]+status_options+html_content.split("{statuses}")[1]
    # Возвращаем HTML-страницу с динамическими статусами
    return HTMLResponse(result)





@app.post("/page_add_new")
async def add_parcel(request: Request, status: int = Form(...), cargo: str = Form(...)):
    session = SessionLocal()
    try:
        # Создание нового объекта посылки
        new_parcel = Parcel(
            current_status=status,
            cargo=cargo
        )
        session.add(new_parcel)
        session.flush()  # Получаем ID нового объекта без коммита

        # Сохраняем изменения
        session.commit()

        # Получаем ID нового элемента
        new_id = new_parcel.id_parcels

        # Перенаправление на страницу с параметрами start_id и end_id
        return RedirectResponse(
            url=f"/view_parcels?start_id={new_id}&end_id={new_id}",
            status_code=303
        )

    except SQLAlchemyError as e:
        session.rollback()
        return {"error": f"Ошибка при добавлении посылки: {e}"}
    finally:
        session.close()