#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from urllib.parse import urlparse, parse_qs

from iocbio.gel.db.connection_parameters.connection_parameters import ConnectionParameters


class PostgreSQLParameters(ConnectionParameters):
    @staticmethod
    def to_connection_string(host, port, user, password, db_name, schema, ssl_mode) -> str:
        connection_string = "postgresql://"
        if user:
            connection_string += user
            if password:
                connection_string += f":{password}"
            connection_string += "@"
        if host:
            connection_string += host
        if port:
            connection_string += f":{port}"
        if db_name:
            connection_string += f"/{db_name}"
        options = []
        if ssl_mode:
            options.append(f"sslmode={ssl_mode}")
        if schema:
            options.append(f"options=-csearch_path={schema}")
        if options:
            connection_string += "?" + "&".join(options)
        return connection_string

    @staticmethod
    def from_connection_string(connection_string: str) -> dict:
        """
        Parse field values from the previously saved connection string.
        """
        params = {}
        if not connection_string or not connection_string.startswith("postgresql"):
            return params

        p = urlparse(connection_string)
        q = parse_qs(p.query)

        params = dict(
            host=p.hostname,
            db=p.path[1:] if p.path and len(p.path) > 1 else "",
            user=p.username,
            password=p.password,
        )

        if p.port:
            params["port"] = str(p.port)

        if len(q.get("sslmode", [])) == 1:
            params["ssl"] = q["sslmode"][0]

        if len(q.get("options", [])) == 1 and q["options"][0].startswith("-csearch_path="):
            params["schema"] = q["options"][0][len("-csearch_path=") :]

        return params
