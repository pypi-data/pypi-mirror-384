import asyncio
import multiprocessing
import queue
import threading


class RunParallel:
    """
    Menjalankan program secara bersamaan.

    - `class RunParallel` didesain hanya untuk pemrosesan data saja.
    - Penggunaannya `class RunParallel` dengan cara membuat instance
      sub class beserta data yg akan diproses, kemudian panggil fungsi
      yg dipilih `run_asyncio / run_multi_threading / run_multi_processing`,
      kemudian dapatkan hasilnya.
    - `class RunParallel` tidak didesain untuk menyimpan data, karena
      setiap module terutama module `multiprocessing` tidak dapat mengakses
      data kelas dari proses yg berbeda.
    - Semua methods akan dijalankan secara paralel kecuali method dengan
      nama yg diawali underscore `_`
    - Method untuk multithreading/multiprocessing harus memiliki 2
      parameter, yaitu: `result: dict` dan `q: queue.Queue`. Parameter
      `result` digunakan untuk memberikan return value dari method, dan
      Parameter `q` digunakan untuk mengirim data antar proses.
    - Method untuk asyncio harus menggunakan keyword `async def`, dan
      untuk perpindahan antar kode menggunakan `await asyncio.sleep(0)`,
      dan keyword `return` untuk memberikan return value.
    - Return Value berupa dictionary dengan key adalah nama function,
      dan value adalah return value dari setiap fungsi
    - Menjalankan Multiprocessing harus berada dalam blok
      `if __name__ == "__main__":` karena area global pada program akan
      diproses lagi. Terutama pada sistem operasi windows.
    - `run_asyncio()` akan menjalankan kode dalam satu program, hanya
      saja alur program dapat berpindah-pindah menggunkan
      `await asyncio.sleep(0)`.
    - `run_multi_threading()` akan menjalankan program dalam satu CPU,
      hanya saja dalam thread yang berbeda. Walaupun tidak benar-benar
      berjalan secara bersamaan namun bisa meningkatkan kecepatan
      penyelesaian program, dan dapat saling mengakses resource antar
      program.  Akses resource antar program bisa secara langsung maupun
      menggunakan parameter yang sudah disediakan yaitu `result: dict`
      dan `q: queue.Queue`.
    - `run_multi_processing()` akan menjalankan program dengan beberapa
      CPU. Program akan dibuatkan environment sendiri yang terpisah dari
      program induk. Keuntungannya adalah program dapat benar-benar berjalan
      bersamaan, namun tidak dapat saling mengakses resource secara langsung.
      Akses resource menggunakan parameter yang sudah disediakan yaitu
      `result: dict` dan `q: queue.Queue`.

    ```py
    class ExampleRunParallel(RunParallel):
        z = "ini"

        def __init__(self) -> None:
            self.pop = random.randint(0, 100)

        def _set_property_here(self, v):
            self.prop = v

        def a(self, result: dict, q: queue.Queue):
            result["z"] = self.z
            result["pop"] = self.pop
            result["a"] = "a"
            q.put("from a 1")
            q.put("from a 2")

        def b(self, result: dict, q: queue.Queue):
            result["z"] = self.z
            result["pop"] = self.pop
            result["b"] = "b"
            result["q_get"] = q.get()

        def c(self, result: dict, q: queue.Queue):
            result["z"] = self.z
            result["pop"] = self.pop
            result["c"] = "c"
            result["q_get"] = q.get()

        async def d(self):
            print("hello")
            await asyncio.sleep(0)
            print("hello")

            result = {}
            result["z"] = self.z
            result["pop"] = self.pop
            result["d"] = "d"
            return result

        async def e(self):
            print("world")
            await asyncio.sleep(0)
            print("world")

            result = {}
            result["z"] = self.z
            result["pop"] = self.pop
            result["e"] = "e"
            return result

    if __name__ == "__main__":
        print(ExampleRunParallel().run_asyncio())
        print(ExampleRunParallel().run_multi_threading())
        print(ExampleRunParallel().run_multi_processing())
    ```
    """

    def get_all_instance_methods(self, coroutine):
        c = set(dir(__class__))
        t = (x for x in dir(self) if x not in c)
        r = []
        for x in t:
            if not x.startswith("_"):
                a = getattr(self, x)
                if callable(a) and asyncio.iscoroutinefunction(a) == coroutine:
                    r.append(a)
        return r
        # return tuple(
        #     a
        #     for x in t
        #     if callable(a := getattr(self, x))
        #     and not x.startswith("_")
        #     and asyncio.iscoroutinefunction(a) == coroutine
        # )

    def run_asyncio(self):
        m = self.get_all_instance_methods(coroutine=True)
        a = self.module_asyncio(*m)
        return self.dict_results(m, a)

    def run_multi_threading(self):
        m = self.get_all_instance_methods(coroutine=False)
        a = self.module_threading(*m)
        return self.dict_results(m, a)

    def run_multi_processing(self):
        m = self.get_all_instance_methods(coroutine=False)
        a = self.module_multiprocessing(*m)
        return self.dict_results(m, a)

    def dict_results(self, names, results):
        return dict(zip((x.__name__ for x in names), results))

    def module_asyncio(self, *args):
        async def main(*args):
            return await asyncio.gather(*(x() for x in args))

        return asyncio.run(main(*args))

    def module_threading(self, *args):
        a = tuple(dict() for _ in args)
        q = queue.Queue()
        r = []
        for i, v in enumerate(args):
            t = threading.Thread(target=v, args=(a[i], q))
            r.append(t)
        # r = tuple(
        #     threading.Thread(target=v, args=(a[i], q)) for i, v in enumerate(args)
        # )
        for i in r:
            i.start()
        for i in r:
            i.join()
        return a

    def module_multiprocessing(self, *args):
        m = multiprocessing.Manager()
        q = m.Queue()
        a = tuple(m.dict() for _ in args)
        r = []
        for i, v in enumerate(args):
            t = multiprocessing.Process(target=v, args=(a[i], q))
            r.append(t)
        # r = tuple(
        #     multiprocessing.Process(target=v, args=(a[i], q))
        #     for i, v in enumerate(args)
        # )
        for i in r:
            i.start()
        for i in r:
            i.join()
        return (i.copy() for i in a)
