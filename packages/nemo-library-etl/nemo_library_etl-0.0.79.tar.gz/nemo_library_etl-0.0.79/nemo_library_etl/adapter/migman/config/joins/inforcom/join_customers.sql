SELECT RELFIRMA.FIRMANR as "S_Kunde.Kunde",
  null as "S_Adresse.AdressNr",
  RELANSCH.Name1 as "S_Adresse.Name1",
  RELANSCH.Staat as "S_Adresse.Staat",
  RELANSCH.Ort as "S_Adresse.Ort",
  RELFIRMA.FIRMANR as "S_Adresse.Suchbegriff",
  null as "S_Adresse.Selektion",
  null as "S_Adresse.BriefAnrede",
  null as "S_Adresse.Anrede",
  null as "S_Adresse.Titel",
  null as "S_Adresse.Vorname",
  RELANSCH.Name2 as "S_Adresse.Name2",
  RELANSCH.Name3 as "S_Adresse.Name3",
  RELANSCH.PLZORT as "S_Adresse.PLZ",
  null as "S_Adresse.CityPrefix",
  null as "S_Adresse.CityPostfix",
  null as "S_Adresse.StreetPrefix",
  RELANSCH.Strasse as "S_Adresse.Strasse",
  null as "S_Adresse.StreetPostfix",
  null as "S_Adresse.Hausnummer",
  RELANSCH.Land as "S_Adresse.Bundesland",
  RELANSCH.PLZPostfach as "S_Adresse.PLZ_Postfach",
  RELANSCH.Postfach as "S_Adresse.Postfach",
  true as "S_Adresse.Telefonbuch",
  RELKOMM_EMAIL.Nummer as "S_Adresse.EMail",
  RELKOMM_HOMEPAGE.Nummer as "S_Adresse.HomePage",
  RELKOMM_MOBILE.Nummer as "S_Adresse.Handy",
  RELKOMM_PHONE.Nummer as "S_Adresse.Telefon",
  null as "S_Adresse.AutoTelefon",
  RELKOMM_FAX.Nummer as "S_Adresse.Telefax",
  RELKOMM_PHONE2.Nummer as "S_Adresse.Telefon2",
  RELKOMM_FAX2.Nummer as "S_Adresse.Telefax2",
  null as "S_Adresse.Longitude",
  null as "S_Adresse.Latitude",
  RELFIRMA.Suchbegriff as "S_Kunde.Suchbegriff",
  null as "S_Kunde.Selektion",
  null as "S_Kunde.Verteilergruppe",
  RELFIRMA.FGKNZ_1 as "S_Kunde.Branche",
  RELANSCH.LandKng as "S_Kunde.Region"
FROM RELADRESSE
  LEFT JOIN RELFIRMA ON RELADRESSE.FIRMANR = RELFIRMA.FIRMANR
  LEFT JOIN RELANSCH ON RELADRESSE.ANSCHRIFTNR = RELANSCH.ANSCHRIFTNR
  LEFT JOIN RELKOMM AS RELKOMM_PHONE ON RELADRESSE.ADRESSENR = RELKOMM_PHONE.ADRESSENR
  AND RELKOMM_PHONE.KOMART = 1 -- phone
  LEFT JOIN RELKOMM AS RELKOMM_FAX ON RELADRESSE.ADRESSENR = RELKOMM_FAX.ADRESSENR
  AND RELKOMM_FAX.KOMART = 2 -- fax
  LEFT JOIN RELKOMM AS RELKOMM_MOBILE ON RELADRESSE.ADRESSENR = RELKOMM_MOBILE.ADRESSENR
  AND RELKOMM_MOBILE.KOMART = 3 -- mobile
  LEFT JOIN RELKOMM AS RELKOMM_EMAIL ON RELADRESSE.ADRESSENR = RELKOMM_EMAIL.ADRESSENR
  AND RELKOMM_EMAIL.KOMART = 4 -- email
  LEFT JOIN RELKOMM AS RELKOMM_HOMEPAGE ON RELADRESSE.ADRESSENR = RELKOMM_HOMEPAGE.ADRESSENR
  AND RELKOMM_HOMEPAGE.KOMART = 5 -- homepage
  LEFT JOIN RELKOMM AS RELKOMM_PHONE2 ON RELADRESSE.ADRESSENR = RELKOMM_PHONE2.ADRESSENR
  AND RELKOMM_PHONE2.KOMART IN (11, 12) -- phone2
  LEFT JOIN RELKOMM AS RELKOMM_FAX2 ON RELADRESSE.ADRESSENR = RELKOMM_FAX2.ADRESSENR
  AND RELKOMM_FAX2.KOMART = 21 -- fax2
WHERE RELFIRMA.VERWENDUNG1 = 1 -- customer
  AND RELADRESSE.PERSONNR is NULL
  AND RELANSCH.VERWENDUNG1 = 1 -- main address
ORDER BY RELFIRMA.FIRMANR 
LIMIT 100