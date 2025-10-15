SELECT
        RELFIRMA.FIRMANR        as "S_Lieferant.Lieferant"                  ,
        null                    as "S_Adresse.AdressNr"                     ,
        RELANSCH.Name1          as "S_Adresse.Name1"                        ,
        RELANSCH.Staat          as "S_Adresse.Staat"                        ,
        RELANSCH.Ort            as "S_Adresse.Ort"                          ,
        RELFIRMA.FIRMANR        as "S_Adresse.Suchbegriff"                  ,
        null                    as "S_Adresse.Selektion"                    ,
        null                    as "S_Adresse.BriefAnrede"                  ,
        null                    as "S_Adresse.Anrede"                       ,
        null                    as "S_Adresse.Titel"                        ,
        null                    as "S_Adresse.Vorname"                      ,
        RELANSCH.Name2          as "S_Adresse.Name2"                        ,
        RELANSCH.Name3          as "S_Adresse.Name3"                        ,
        RELANSCH.PLZORT         as "S_Adresse.PLZ"                          ,
        null                    as "S_Adresse.CityPrefix"                   ,
        null                    as "S_Adresse.CityPostfix"                  ,
        null                    as "S_Adresse.StreetPrefix"                 ,
        RELANSCH.Strasse        as "S_Adresse.Strasse"                      ,
        null                    as "S_Adresse.StreetPostfix"                ,
        null                    as "S_Adresse.Hausnummer"                   ,
        RELANSCH.Land           as "S_Adresse.Bundesland"                   ,
        RELANSCH.PLZPostfach    as "S_Adresse.PLZ_Postfach"                 ,
        RELANSCH.Postfach       as "S_Adresse.Postfach"                     ,
        true                    as "S_Adresse.Telefonbuch"                  ,
        RELKOMM_EMAIL.Nummer    as "S_Adresse.EMail"                        ,
        RELKOMM_HOMEPAGE.Nummer as "S_Adresse.HomePage"                     ,
        RELKOMM_MOBILE.Nummer   as "S_Adresse.Handy"                        ,
        RELKOMM_PHONE.Nummer    as "S_Adresse.Telefon"                      ,
        null                    as "S_Adresse.AutoTelefon"                  ,
        RELKOMM_FAX.Nummer      as "S_Adresse.Telefax"                      ,
        RELKOMM_PHONE2.Nummer   as "S_Adresse.Telefon2"                     ,
        RELKOMM_FAX2.Nummer     as "S_Adresse.Telefax2"                     ,
        null                    as "S_Adresse.Longitude"                    ,
        null                    as "S_Adresse.Latitude"                     ,
        RELFIRMA.SUCHBEGRIFF    as "S_Lieferant.Suchbegriff"                ,
        RELFIRMA.FIRMANR        as "S_Lieferant.Selektion"                  ,
        null                    as "S_Lieferant.VerteilerGruppe"            ,
        null                    as "S_Lieferant.Branche"                    ,
        null                    as "S_Lieferant.Betriebskalender"           ,
        null                    as "S_Lieferant.Sachbearbeiter"             ,
        RELANSCH.SPRACHKNZ      as "S_Lieferant.Sprache"                    ,
        RELFIRMA.ABCKLAS        as "S_Lieferant.ABC_Klasse"                 ,
        RELFIRMA.FREMDNR        as "S_Lieferant.Kundennummer"               ,
        RELFIRMA.TAXNO          as "S_Lieferant.inlaendische_SteuerNr"      ,
        null                    as "S_Lieferant.Waehrung"                   ,
        RELFIRMA.USTIDNR        as "S_UStID.UStID"                          ,
        3                       as "S_Lieferant.ZahlungsArt"                ,
        null                    as "S_Lieferant.RemittanceAdvice"           ,
        RELACP.ZBED             as "S_Lieferant.ZahlungsZiel"               ,
        null                    as "S_Lieferant.Kreditlimit"                ,
        1                       as "S_Lieferant.StGr_mit_ST"                ,
        2                       as "S_Lieferant.StGr_ohne_ST"               ,
        3                       as "S_Lieferant.StGrEU_mit_ST"              ,
        4                       as "S_Lieferant.StGrEU_ohne_ST"             ,
        5                       as "S_Lieferant.StGrAus_mit_ST"             ,
        6                       as "S_Lieferant.StGrAus_ohne_ST"            ,
        RELACP.TEXT0            as "S_Lieferant.Lieferbedingung"            ,
        null                    as "S_Lieferant.VersandArt"                 ,
        null                    as "S_Lieferant.Mindestbestellwert"         ,
        null                    as "BBM_WflLockStatus.BBM_WflLockStatus_ID" ,
        null                    as "S_BelegParam.FormularAnzahl"            ,
        null                    as "S_KONTO.sammelkonto"                    ,
        null                    as "S_UStID.bestaetigt"                     ,
        null                    as "S_BankVerb.Bankverbindung"              ,
        null                    as "S_UStID.IsDefault"                      ,
        null                    as "S_Lieferant.CountryOfOrigin"            ,
        null                    as "S_Lieferant.RegionOfOrigin"             ,
        null                    as "S_Lieferant.I_BalanceList"              ,
        null                    as "S_Lieferant.I_NaturalPerson"            ,
        null                    as "S_Lieferant.I_ReportingType"            ,
        null                    as "S_Lieferant.I_BlackList"                ,
        null                    as "S_Lieferant.I_PrepaymentRate"           ,
        null                    as "S_Lieferant.I_PrepaymentType"           ,
        null                    as "S_Lieferant.CtrlGroupStateTax"          ,
        null                    as "S_Lieferant.CtrlGroupStateNoTax"        ,
        null                    as "S_Lieferant.cIN_Certificate_ImpExp"     ,
        null                    as "S_Lieferant.cIN_CIN"                    ,
        null                    as "S_Lieferant.cIN_GSTID"                  ,
        null                    as "S_Lieferant.cIN_PAN"                    ,
        null                    as "S_Lieferant.cIN_TAN"                    ,
        null                    as "S_Lieferant.P_Steuerregister"           ,
        null                    as "S_Lieferant.F_FormNrDomCur"             ,
        null                    as "S_Lieferant.F_FormNrForCur"             ,
        null                    as "S_Lieferant.F_NrForms"                  ,
        null                    as "S_Lieferant.F_ActivitySector"           ,
        null                    as "S_Lieferant.F_Capital"                  ,
        null                    as "S_Lieferant.F_Siret"                    ,
        null                    as "S_Lieferant.F_TradeRegister"            ,
        null                    as "S_Lieferant.cRU_IEC"                    ,
        null                    as "S_Lieferant.cRU_Rclassifyer"            ,
        null                    as "S_Lieferant.cRU_DocIdentPers"           ,
        null                    as "S_Lieferant.cRU_ForeignTaxID"           ,
        null                    as "S_Lieferant.cRU_PrimStRegNr"            ,
        null                    as "S_Lieferant.cRU_PrimStRegDa"            ,
        null                    as "S_Lieferant.cRU_EntCertRegNo"           ,
        null                    as "S_Lieferant.cRU_EntCerRegDate"          ,
        null                    as "S_Lieferant.uCW_FreeDeliveryLimit"
FROM
        RELADRESSE
LEFT JOIN
        RELFIRMA
ON
        RELADRESSE.FIRMANR = RELFIRMA.FIRMANR
LEFT JOIN
        RELANSCH
ON
        RELADRESSE.ANSCHRIFTNR = RELANSCH.ANSCHRIFTNR
LEFT JOIN
        RELKOMM AS RELKOMM_PHONE
ON
        RELADRESSE.ADRESSENR = RELKOMM_PHONE.ADRESSENR
AND     RELKOMM_PHONE.KOMART = 1 -- phone
LEFT JOIN
        RELKOMM AS RELKOMM_FAX
ON
        RELADRESSE.ADRESSENR = RELKOMM_FAX.ADRESSENR
AND     RELKOMM_FAX.KOMART   = 2 -- fax
LEFT JOIN
        RELKOMM AS RELKOMM_MOBILE
ON
        RELADRESSE.ADRESSENR  = RELKOMM_MOBILE.ADRESSENR
AND     RELKOMM_MOBILE.KOMART = 3 -- mobile
LEFT JOIN
        RELKOMM AS RELKOMM_EMAIL
ON
        RELADRESSE.ADRESSENR = RELKOMM_EMAIL.ADRESSENR
AND     RELKOMM_EMAIL.KOMART = 4 -- email
LEFT JOIN
        RELKOMM AS RELKOMM_HOMEPAGE
ON
        RELADRESSE.ADRESSENR    = RELKOMM_HOMEPAGE.ADRESSENR
AND     RELKOMM_HOMEPAGE.KOMART = 5 -- homepage
LEFT JOIN
        RELKOMM AS RELKOMM_PHONE2
ON
        RELADRESSE.ADRESSENR = RELKOMM_PHONE2.ADRESSENR
AND     RELKOMM_PHONE2.KOMART IN (11,
                                  12) -- phone2
LEFT JOIN
        RELKOMM AS RELKOMM_FAX2
ON
        RELADRESSE.ADRESSENR = RELKOMM_FAX2.ADRESSENR
AND     RELKOMM_FAX2.KOMART  = 21 -- fax2
LEFT JOIN
        RELACP
ON
        RELADRESSE.FIRMANR = RELACP.MNR
WHERE
        RELFIRMA.VERWENDUNG1 = 2 -- supplier
AND     RELADRESSE.PERSONNR is NULL
AND     RELANSCH.VERWENDUNG1 = 1 -- main address
ORDER BY
        RELFIRMA.FIRMANR
LIMIT 50