SELECT
    LFA1.LIFNR                AS "S_Lieferant.Lieferant",
    LFA1.ADRNR                AS "S_Adresse.AdressNr",
    LFA1.NAME1                AS "S_Adresse.Name1",
    ADRC.COUNTRY              AS "S_Adresse.Staat",
    ADRC.CITY1                AS "S_Adresse.Ort",
    LFA1.SORT1                AS "S_Adresse.Suchbegriff",
    LFA1.SORT2                AS "S_Adresse.Selektion",
    ADRC.TITLE                AS "S_Adresse.Titel",
    ADRC.NAME2                AS "S_Adresse.Name2",
    ADRC.NAME3                AS "S_Adresse.Name3",
    ADRC.POST_CODE1           AS "S_Adresse.PLZ",
    ADRC.CITY2                AS "S_Adresse.CityPostfix",
    ADRC.STREET               AS "S_Adresse.Strasse",
    ADRC.HOUSE_NUM1           AS "S_Adresse.Hausnummer",
    ADRC.REGION               AS "S_Adresse.Bundesland",
    ADRC.POST_CODE2           AS "S_Adresse.PLZ_Postfach",
    ADRC.PO_BOX               AS "S_Adresse.Postfach",
    ADR6.SMTP_ADDR            AS "S_Adresse.EMail",
    ADR2.TEL_NUMBER           AS "S_Adresse.Telefon",
    ADR3.FAX_NUMBER           AS "S_Adresse.Telefax",
    LFA1.TELF2                AS "S_Adresse.Telefon2",
    LFA1.MCOD1                AS "S_Lieferant.Suchbegriff",
    LFA1.MCOD2                AS "S_Lieferant.Selektion",
    LFA1.BRSCH                AS "S_Lieferant.Branche",
    LFA1.PLKAL                AS "S_Lieferant.Betriebskalender",
    LFA1.BUSAB                AS "S_Lieferant.Sachbearbeiter",
    LFA1.SPRAS                AS "S_Lieferant.Sprache",
    LFA1.STCD1                AS "S_Lieferant.inlaendische_SteuerNr",
    LFA1.STCEG                AS "S_UStID.UStID",
    LFB1.ZWELS                AS "S_Lieferant.ZahlungsArt",
    LFB1.ZTERM                AS "S_Lieferant.ZahlungsZiel",
    LFA1.STKZU                AS "S_UStID.bestaetigt"

FROM LFA1
LEFT JOIN LFB1
    ON LFA1.LIFNR = LFB1.LIFNR
LEFT JOIN ADRC
    ON LFA1.ADRNR = ADRC.ADDRNUMBER
LEFT JOIN ADR2
    ON LFA1.ADRNR = ADR2.ADDRNUMBER
LEFT JOIN ADR3
    ON LFA1.ADRNR = ADR3.ADDRNUMBER
LEFT JOIN ADR6
    ON LFA1.ADRNR = ADR6.ADDRNUMBER;
