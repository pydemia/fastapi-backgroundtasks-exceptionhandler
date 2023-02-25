import os
# from fastapi_app.main import app


if __name__ == "__main__":
    # import multiprocessing
    # mpr.set_start_method("spawn", True)

    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # options = {
    #     "bind": f"{HOST}:{APP_PORT}",
    #     "workers": number_of_workers(),
    # }
    # StandaloneApp(handler_app, options).run()

    import uvicorn

    uvicorn.run("fastapi_app.main:app", host=HOST, port=PORT)
# print("imported")
