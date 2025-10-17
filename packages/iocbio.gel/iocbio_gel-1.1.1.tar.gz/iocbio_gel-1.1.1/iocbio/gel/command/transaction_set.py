#
#  This file is part of IOCBIO Gel.
#
#  SPDX-FileCopyrightText: 2022-2023 IOCBIO Gel Authors
#  SPDX-License-Identifier: GPL-3.0-or-later
#


from typing import List, Callable, Iterable

from sqlalchemy import exc

from iocbio.gel.command.command import Command
from iocbio.gel.command.command_set import CommandSet
from iocbio.gel.db.database_client import DatabaseClient


class TransactionSet(CommandSet):
    def __init__(self, commands: List[Command], db: DatabaseClient):
        super().__init__(commands)
        self.db = db

    def _execute(self, commands: Iterable[Command], method: str) -> list[Callable]:
        """
        Calling just `transaction.commit()` leaves some changes uncommitted, thus calling commit also on the session.
        """
        transaction = self.db.start_transaction()

        try:
            callbacks = super()._execute(commands, method)
            transaction.commit()
            self.db.commit()
            return callbacks
        except exc.SQLAlchemyError as error:
            transaction.rollback()
            raise error
