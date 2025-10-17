/* 
 * konkreetsete auto-id'ga tabelite, kus on palju lisamisi ja kustutamisi
 * id-defragmenteerimiseks funktsioon, mida korrapäraselt (1 kord aastas) välja kutsuda, et vältida overflow-d
 * ei defragmenteeri kui tabeli ID pole veel piisavalt suur (kuna defrag iseenesest pole mingi eesmärk baasis) 
 * eeldab probleemide/logide tabeli olemasolu
 */
 
DROP FUNCTION IF EXISTS bis.f_avoid_overflow();

CREATE OR REPLACE FUNCTION bis.f_avoid_overflow()
RETURNS VOID
SECURITY DEFINER VOLATILE NOT LEAKPROOF PARALLEL UNSAFE LANGUAGE plpgsql AS
$$
begin
    declare
        li_min_id INTEGER := 0;
        li_max_id INTEGER := 0;
        li_threshold INTEGER = 2^29 - 1; -- tugeva reserviga (int jaoks on ülempiir 2 astmel 31 miinus 1) 
        ls_other_msg text;
        ls_other_state text;
    begin
        begin -- bis_trace
            SELECT MIN(id), MAX(id) INTO li_min_id, li_max_id FROM bis.bis_trace; -- min on ainult logimise eesmärgil
            if li_max_id >= li_threshold then
                UPDATE bis.bis_trace SET id = defrag.jrk 
                    FROM (select id, row_number() over (order by id asc) as jrk from bis.bis_trace) as defrag
                    WHERE defrag.id = bis.bis_trace.id;
                PERFORM setval('bis.bis_trace_id_seq'::regclass, (SELECT max(id) FROM bis.bis_trace));
                INSERT INTO bis.bis_trace (processname, flag, content)
                    SELECT 'DEFRAG', 'INFO', 'bis_trace, defrag because threshold ' || li_threshold || ' from ' || li_min_id || '-' || li_max_id || ' to ' || min(id) || '-' || max(id)
                    FROM bis.bis_trace;
            end if;
        exception 
            when others then
                get stacked diagnostics ls_other_msg = MESSAGE_TEXT, ls_other_state = RETURNED_SQLSTATE; 
                INSERT INTO bis.bis_trace (processname, flag, content) VALUES ('DEFRAG', 'bis_trace, defrag error: ' || ls_other_state || ' : ' || ls_other_msg);
        end;

        begin -- bis_agenda
            SELECT MIN(id), MAX(id) INTO li_min_id, li_max_id FROM bis.bis_agenda; -- min on ainult logimise eesmärgil
            if li_max_id >= li_threshold then
                UPDATE bis.bis_agenda SET id = defrag.jrk 
                    FROM (select id, row_number() over (order by id asc) as jrk from bis.bis_agenda) as defrag
                    WHERE defrag.id = bis.bis_agenda.id;
                PERFORM setval('bis.bis_agenda_id_seq'::regclass, (SELECT max(id) FROM bis.bis_agenda));
                INSERT INTO bis.bis_trace (processname, flag, content)
                    SELECT 'DEFRAG', 'INFO', 'bis_agenda, defrag because threshold ' || li_threshold || ' from ' || li_min_id || '-' || li_max_id || ' to ' || min(id) || '-' || max(id)
                    FROM bis.bis_agenda;
            end if;
        exception 
            when others then
                get stacked diagnostics ls_other_msg = MESSAGE_TEXT, ls_other_state = RETURNED_SQLSTATE; 
                INSERT INTO bis.bis_trace (processname, flag, content) VALUES ('DEFRAG', 'bis_agenda, defrag error: ' || ls_other_state || ' : ' || ls_other_msg);
        end;

        begin -- bis_worker
            SELECT MIN(id), MAX(id) INTO li_min_id, li_max_id FROM bis.bis_worker; -- min on ainult logimise eesmärgil
            if li_max_id >= li_threshold then
                UPDATE bis.bis_worker SET id = defrag.jrk 
                    FROM (select id, row_number() over (order by id asc) as jrk from bis.bis_worker) as defrag
                    WHERE defrag.id = bis.bis_worker.id;
                PERFORM setval('bis.bis_worker_id_seq'::regclass, (SELECT max(id) FROM bis.bis_worker));
                INSERT INTO bis.bis_trace (processname, flag, content)
                    SELECT 'DEFRAG', 'INFO', 'bis_worker, defrag because threshold ' || li_threshold || ' from ' || li_min_id || '-' || li_max_id || ' to ' || min(id) || '-' || max(id)
                    FROM bis.bis_worker;
            end if;
        exception 
            when others then
                get stacked diagnostics ls_other_msg = MESSAGE_TEXT, ls_other_state = RETURNED_SQLSTATE; 
                INSERT INTO bis.bis_trace (processname, flag, content) VALUES ('DEFRAG', 'bis_worker, defrag error: ' || ls_other_state || ' : ' || ls_other_msg);
        end;

        
    end;
end
$$
;
COMMENT ON FUNCTION bis.f_avoid_overflow IS 'suure käibega tabelite int-pk ületäite vältimiseks korraliselt käivitada';
