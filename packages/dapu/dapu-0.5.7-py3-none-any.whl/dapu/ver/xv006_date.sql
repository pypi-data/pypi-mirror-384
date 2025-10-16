-- vajalik juhul, kui vaja TZ TS tüübist saada teha indeks 
CREATE FUNCTION dwh.f_date(ts timestamptz) 
RETURNS date 
SECURITY INVOKER IMMUTABLE AS
$code$
SELECT ts::date
$code$ LANGUAGE SQL ;;

COMMENT ON FUNCTION dwh.f_date(timestamptz) IS 'indeksite jaoks timestambi IMMUTABLE-ks tegemine';
