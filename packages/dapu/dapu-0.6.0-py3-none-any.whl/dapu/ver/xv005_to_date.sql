/*
    Oma funktsion konvertimaks stringe (XML andmetes on sellised) kuupäevadeks
    On eesti ja on inglise formaadis (vb ka ISO formaadis)
    kui PG standard on to_date(string, format)
    siis see on to_date_formats(string, format-array)
    vigade korral on tulemuseks NULL
    nt select dwh.to_date_formats('sodinekuupäev', array['DD.MM.YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD'])
    on vaja kasutada parallel unsafe deklaratsiooni
*/

-- tegelikult on see leakproof, aga selliste jaoks on vaja superuserit

create or replace function dwh.to_date_formats(as_str text, aa_formats text[]) 
returns date 
IMMUTABLE RETURNS NULL ON NULL INPUT SECURITY INVOKER PARALLEL UNSAFE 
AS 
$code$ 
begin
    if aa_formats is null OR array_length(aa_formats, 1) is null then -- tühja massiivi pikkus pole mitte 0 (nagu tundub loomulik), vaid NULL
        return null;
    end if;
    return to_date(as_str, aa_formats[1]); 
EXCEPTION
    WHEN others THEN
        -- kui massiivi esimese elemendiga tekkis viga, siis lühendame masiivi ja proovime uuesti
        -- lühendamiseks eemaldame massiivist esimese formaadi (kui see kordus tagapool, siis eemadatakse ka kordus)
        return to_date_formats(as_str, array_remove(aa_formats, aa_formats[1])); 
end 
$code$ LANGUAGE plpgsql ;;

COMMENT ON FUNCTION dwh.to_date_formats(text, text[]) IS 'kasutada to_date asemel mitme formaadi katsetamiseks ja veaolukorra vältimiseks';
