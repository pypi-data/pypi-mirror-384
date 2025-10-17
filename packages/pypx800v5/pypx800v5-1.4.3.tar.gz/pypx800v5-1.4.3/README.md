# pypx800v5 - Python GCE IPX800 V5

Control the IPX800 V5, its extensions and objects:

- Thermostat
- Counter
- Tempo
- X-8R
- X-8D
- X-24D
- X-Dimmer
- X-PWM
- X-THL
- X-4VR
- X-4FP
- X-Display (v1 and v2)

## IPX800 parameters

- host: ip or hostname (mandatory)
- port: (default: `80`)
- api_key: (mandatory)
- request_timeout: timeout for request in seconds (default: `30`)
- request_retries_count: retry request if an error occured (default: `5`)
- request_retries_delay: delay in seconds before trying request (default: `0.5`)
- session: aiohttp.client.ClientSession

## Example

```python
import asyncio

from pypx800v5 import *


async def main():
    async with IPX800(host='192.168.1.123', api_key='xxx') as ipx:
        await ipx.ping()
        await ipx.init_config()

        relay = IPX800Relay(ipx, 0)
        print(await relay.status)
        await relay.on()

        opencoll = IPX800OpenColl(ipx, 0)
        print(await opencoll.status)
        await opencoll.on()

        input = IPX800DigitalInput(ipx, 2)
        print(await input.status)

        input = IPX800AnalogInput(ipx, 0)
        print(await input.status)
        
        input = IPX800OptoInput(ipx, 0)
        print(await input.status)

        light = X8R(ipx, 0, 7)
        print(await light.status)
        await light.on()

        pwm = XPWM(ipx, 0, 6)
        print(await pwm.status)
        print(await pwm.level)
        await pwm.set_level(90)

        light = XDimmer(ipx, 0, 2)
        print(await light.status)
        print(await light.level)
        await light.on()

        input = X24D(ipx, 0, 14)
        print(await input.status)

        capteur = XTHL(ipx, 0)
        print(await capteur.temperature)
        print(await capteur.humidity)
        print(await capteur.luminosity)

        tempo = Tempo(ipx, 0)
        print(tempo.name)
        print(await tempo.status)
        print(await tempo.time)

        x010v_output = X010V(ipx, 0, 2)
        print(await x010v_output.status)
        print(await x010v_output.level)
        await x010v_output.on()

        xdisplay = XDisplay(ipx, 0)
        await xdisplay.refresh_screens()
        for screen in xdisplay.screens:
            print(f"{screen.id} - {screen.name} - {screen.type}")
        print(f"screen status ? {await xdisplay.screen_status}")
        print(f"screen locked ? {await xdisplay.screen_lock_status}")
        print(f"current screen ? {await xdisplay.current_screen_id}")
        await xdisplay.set_screen(0)
        print(f"current screen ? {await xdisplay.current_screen_id}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

```
