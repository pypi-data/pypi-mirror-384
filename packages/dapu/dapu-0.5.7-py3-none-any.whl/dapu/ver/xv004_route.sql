DELETE FROM bis.bis_route WHERE TRUE;

INSERT INTO bis.bis_route (code, name, connection_from)
	VALUES ('inner', 'Baasisisesed liikumised', 'DWH_LOADER_URL');
