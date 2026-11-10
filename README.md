# Storitev Server Room SOAP

Spletna storitev SOAP, ki upravlja tri simulirane naprave v strežniški
sobi. Namenski konzolni odjemalec demonstrira vse operacije.

Arhitektura ustreza vzorcu **storitveno podprta komunikacija**
(angl. *service-assisted communication*): odjemalec nikoli ne
komunicira z napravo neposredno. Kliče spletno storitev, storitev pa
vrne podatke o napravi in izvede ukaze. Naprave in senzorji so
simulirani v pomnilniku procesa storitve.

## Arhitektura

    client/client.py  --SOAP-->  server/service.py  -->  server/devices.py
      (Zeep proxy)               (Spyne adapter)        (podatki v pomnilniku)

- `server/devices.py` vsebuje podatke o napravah in logiko simulacije.
  Ne uvaža Spyne, nima HTTP-ja in ne ve, da bo izpostavljen prek SOAP.
- `server/service.py` je SOAP adapter. Bere slovarje iz `devices.py`
  in jih ovije v modele Spyne. Tu ni poslovne logike.
- `server/app.py` poveže storitev v WSGI aplikacijo.
- `run_server.py` zažene strežnik na vratih 8007.
- `client/client.py` je interaktivni konzolni odjemalec (Zeep).

Ločevanje je pomembno: domenska plast ne ve, da je izpostavljena prek
SOAP. Če bi kasneje prešli na REST ali gRPC, bi bilo treba spremeniti
samo `service.py` in `app.py`.

## Naprave in senzorji

| Naprava                          | Serijska št.   | Proizvajalec |
|----------------------------------|----------------|--------------|
| NetShelter Rack PDU 2026         | PDU-2026-0001  | APC          |
| EnvGuard Environmental Sensor    | ENV-2026-0001  | Sensirion    |
| AxisEye RackCam 4K               | CAM-2026-0001  | Axis         |

| Senzor                       | Naprava | Enota                  |
|------------------------------|---------|------------------------|
| PDU-2026-0001-current        | PDU     | A                      |
| PDU-2026-0001-temp           | PDU     | C                      |
| ENV-2026-0001-temperature    | ENV     | C                      |
| ENV-2026-0001-door           | ENV     | enum (open/closed/fault) |
| CAM-2026-0001-motion         | CAM     | bool (true/false)      |

Skupaj: 3 naprave, 5 senzorjev. Vrednosti pokrivajo numerični, enum
in boolean tip.

## Operacije

| Operacija                        | Namen                                          |
|----------------------------------|------------------------------------------------|
| `get_device_states()`            | Vrne vse naprave in njihovo stanje ON/OFF      |
| `set_device_state(serial, st)`   | Nastavi napravo na ON ali OFF                  |
| `get_sensors(serial)`            | Vrne senzorje ene naprave                      |
| `get_readings(serial)`           | Vrne eno svežo meritev na senzor               |

Naloga zahteva štiri kategorije: branje stanja, pisanje stanja,
krmiljenje, seznam senzorjev. Kontrolne operacije iz naloge 3
(PDU/ENV/CAM) so bile namerno umaknjene; spremembo stanja naprav
pokriva `set_device_state`, branje stanja in seznam senzorjev pa se
preslikata 1:1 na ločene operacije, ki ohranijo WSDL ekspliciten in
samoopisen. Zeep vsako izpostavi kot samostojno metodo.

`set_device_state` je implementirana skladno z vzorcem enosmerne
komunikacije (one-way / fire-and-forget): operacija ne vrača podatkov
(odzivno sporočilo v WSDL je prazno), zato odjemalec izpiše zahtevani
ukaz, ne pa potrditve strežnika.

`get_readings` ni v štirih zahtevanih kategorijah, a naloga zahteva,
da so vrednosti senzorjev del sporočil. Obstaja zato, da odjemalec
lahko vidi dejansko vrednost.

## Namestitev

Razvito in preizkušeno na Python 3.11.

    pip install -r requirements.txt

## Zagon

Terminal 1:

    python run_server.py

Strežnik posluša na `http://127.0.0.1:8007`. WSDL je na
`http://127.0.0.1:8007/?wsdl`.

Terminal 2:

    cd client
    python client.py

## Preizkus delovanja

Odjemalec ponudi meni z naslednjimi možnostmi:

1. Prikaži stanja vseh naprav — prikaže vse tri naprave in njihovo stanje.
2. Nastavi stanje naprave — vpraša za serijsko številko in novo stanje
   (ON/OFF). Primer: `PDU-2026-0001`, `OFF`.
3. Prikaži senzorje naprave — seznam senzorjev za izbrano napravo.
4. Prikaži meritve naprave — sveže meritve z časovnimi značkami UTC.
5. Registriraj novega uporabnika — operacija `register_user`.
6. Prijava — nastavi WS-Security poverilnice za naslednje klice.
7. Demo klici — prežene vse operacije enkrat in namerno sproži dve
   napaki (zasedeno uporabniško ime, neveljavno stanje).
0. Izhod.

Če pošljete neveljavne podatke (neobstoječa naprava, neveljavno
stanje, napačne poverilnice), strežnik vrne
SOAP napako, odjemalec pa jo izpiše. Vse napake klicatelja uporabljajo
`faultcode="Client"` (dogovor: Client = napačen vhod, Server = notranja
napaka). Primer:

- `get_sensors("XX-0000")` → `SOAP napaka: unknown device: XX-0000`
- `set_device_state("PDU-2026-0001", "BROKEN")` → `SOAP napaka: invalid state: BROKEN`

## Zasnova in odločitve (za zagovor)

**Zakaj simulirane naprave?**
Naloga dovoljuje simulirane podatke senzorjev. Naprave živijo v
slovarju v pomnilniku procesa storitve in vztrajajo, dokler proces
teče. Vrednosti meritev se ustvarijo na novo ob vsakem klicu, zato
odjemalec vidi spremembe skozi čas.

**Zakaj je vrednost senzorja shranjena kot niz?**
Senzorji vračajo različne tipe (numerični, enum, boolean). Shranjevanje
v niz ohrani en sam tip sporočila za vse meritve in se izogne
polimorfnim SOAP shemam, kar bi bilo precejšnje dodatno delo brez
koristi za oceno. Polje `unit` na senzorju pove odjemalcu, kako
vrednost interpretirati.

**Kaj pa avtentikacija?**
Implementirana je prek WS-Security slogovne glave SOAP
(`server/security/headers.py`): vsak klic nosi glavo `Security` z
`UsernameToken` (uporabniško ime + geslo v odprtem besedilu — prek
TLS v produkciji). Glava je v imenskem prostoru storitve
(`serverroom.soap`) namesto OASIS WSSE, ker Spyne z glavo v tujem
imenskem prostoru generira nerešljivo referenco na `wsdl:message`
([arskom/spyne#419](https://github.com/arskom/spyne/issues/419));
dodan `resolve_namespace` v `headers.py` to zaobide, struktura glave
pa ostane zvesta profilu UsernameToken. Uporabniki so registrirani prek operacije
`register_user` in shranjeni v `users.json` (gesla samo kot
PBKDF2-SHA256 hash s soljo; datoteka je v `.gitignore`). Vsaka
operacija preverja vlogo: `reader` sme brati, `writer` sme tudi
pisati stanje naprav. Neveljavne poverilnice ali premajhna vloga
sprožijo SOAP napako. Vezava na `127.0.0.1` je razvojna privzetska
vrednost — nikoli je ne izpostavite javnemu omrežju takšne, kot je.

**Kaj potem pomeni "varen dostop" prek vmesnega sloja?**
Da se odjemalec nikoli ne dotakne naprav neposredno. Ves dostop gre
skozi storitveni sloj, ki preveri vhod (WS-Security glava) in ob
neveljavnih zahtevah sproži SOAP napako.

**Beleženje dogodkov na strežniški strani.**
`run_server.py` enkrat nastavi stdlib `logging` (konzola + datoteka
`server.log`, ki je v `.gitignore`). Vsaka operacija v
`server/service.py` beleži en `log.info` (klicatelj iz WS-Security
glave, operacija, argumenti — gesla ne beležimo), ob neuspeli
avtentikaciji pa `_require_role` beleži `log.warning`.

**Časovne značke in enote.**
Vse časovne značke se ustvarijo z `datetime.now(timezone.utc)` —
časovno občutljive, na žici v ISO 8601. Pomembno zato, ker naloga
omenja globalno občinstvo. Enote so shranjene kot nizi (`C`, `A`,
`enum`, `bool`), kar omogoča, da odjemalec sam pretvori v °F ali
drugo enoto, če je treba. Pretvorba ni implementirana.

**Odjemalec ni WCF Test Client.**
Odjemalec ni WCF Test Client ali podobno generično orodje. Je namenski
interaktivni konzolni odjemalec (`client/client.py`), ki demonstrira
točno tiste operacije, ki jih naloga zahteva, s slovenskim menijem in
obravnavo napak na dveh ravneh.