# -*- coding: utf-8 -*-

import logging
import sdtp

def main():
    logging.basicConfig(
        filename="sdtp.log", level = logging.INFO,
        format="%(asctime)s %(levelname)-4.4s %(module)-6.6s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    logger = logging.getLogger(__name__)
    logger.info("*********** sdtp - Seven Days To Py ***********")
    controller = sdtp.Controller()
    controller.start()
    try:
        controller.join()
    except KeyboardInterrupt:
        controller.stop()
        controller.join()

if __name__ == "__main__":
    main()
