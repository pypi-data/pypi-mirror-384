#
# GAMS - General Algebraic Modeling System Python API
#
# Copyright (c) 2017-2025 GAMS Development Corp. <support@gams.com>
# Copyright (c) 2017-2025 GAMS Software GmbH <support@gams.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from gams.connect.agents.connectagent import ConnectAgent
from gams.core.embedded import ECGAMSDatabase
from gams.core.gmd import *
import gams.transfer as gt
import pandas as pd


class GAMSWriter(ConnectAgent):

    def __init__(self, cdb, inst, agent_index):
        super().__init__(cdb, inst, agent_index)
        if not (self._cdb.ecdb and isinstance(self._cdb.ecdb, ECGAMSDatabase)):
            self._connect_error("GAMSWriter is running without GAMS context.")
        self._parse_options(self._inst)

    def _parse_options(self, inst):
        self._symbols = inst["symbols"]
        self._duplicate_records = inst["duplicateRecords"]
        self._trace = inst["trace"]
        self._merge_type = inst["mergeType"]
        self._domain_check_type = inst["domainCheckType"]
        self._write_all = self._symbols == "all"

    def execute(self):
        if self._trace > 0:
            self._log_instructions(self._inst, self._inst_raw)
            self._describe_container(self._cdb.container, "Connect Container:")

        elif self._cdb.ecdb.arguments.startswith(
            "@connectOut"
        ):  # we run with GAMS cmd parameter connectOut
            self._connect_error("GAMSWriter not available for connectOut scripts.")

        drmap = {"none": False, "first": "first", "last": "last"}
        write_container = self._cdb.container


        # collect target symbol names
        sym_map = {}  # newName->sym
        if self._write_all:
            sym_map = {s: {"name": s} for s in write_container.listSymbols()}
        else:
            for sym in self._symbols:
                sym_map[self._dict_get(sym, "newName", sym["name"])] = sym

        # check that target symbols exist in GAMS database
        target_sym_names = list(sym_map.keys())
        for sym_t in target_sym_names.copy():
            try:
                self._symbols_exist_gmd(self._cdb.ecdb.db._gmd, sym_t)
            except:
                missing = True
            else:  # if no exception was raised, we have a symbol in the GAMS database and can continue with the next symbol
                continue

            # the symbol was not found in the GAMS database and we need to check the GMD object containing symbols with unknown dimension
            if gmdHandleToPtr(self._cdb.ecdb._gmdud) is not None:
                rc = new_intp()
                symPtr = gmdFindSymbolPy(self._cdb.ecdb._gmdud, sym_t, rc)
                rc_val = intp_value(rc)
                delete_intp(rc)
                if rc_val:
                    missing = False
                    sym_type = self._cdb.container[sym_map[sym_t]["name"]]._gams_type
                    dimension = self._cdb.container[sym_map[sym_t]["name"]].dimension

                    rc, user_info, _, _ = gmdSymbolInfo(self._cdb.ecdb._gmdud, symPtr, GMD_USERINFO)
                    self._cdb._ecdb._check_for_gmd_error(rc, self._cdb.ecdb._gmdud)
                    rc, _, _, sym_text = gmdSymbolInfo(self._cdb.ecdb._gmdud, symPtr, GMD_EXPLTEXT)
                    self._cdb._ecdb._check_for_gmd_error(rc, self._cdb.ecdb._gmdud)

                    rc = new_intp()
                    gmdAddSymbolPy(
                        self._cdb.ecdb._gmd,
                        sym_t,
                        dimension,
                        sym_type,
                        user_info,
                        sym_text,
                        rc,
                    )
                    rc_val = intp_value(rc)
                    delete_intp(rc)
                    self._cdb._ecdb._check_for_gmd_error(rc_val)
            if missing:
                if self._write_all:
                    target_sym_names.remove(sym_t)
                    if self._trace > 0:
                        self._cdb.print_log(
                            f"Skipping symbol '{sym_t}' since it does not exist in the GAMS database."
                        )
                else:
                    self._symbols_exist_gmd(self._cdb.ecdb.db._gmd, sym_t)

        if self._write_all:
            if self._trace > 2:
                for name in target_sym_names:
                    sym = write_container[name]
                    self._cdb.print_log(
                        f"Connect Container symbol={name}:\n {sym.records}\n"
                    )
            if self._duplicate_records != "all":
                # copy Connect container to avoid altering the Connect database
                write_container = gt.Container(
                    self._cdb.container, system_directory=self._system_directory
                )
                write_container.dropDuplicateRecords(
                    symbols=target_sym_names,
                    keep=drmap[self._duplicate_records]
                )
            if not write_container.hasDuplicateRecords(symbols=target_sym_names):
                write_container.write(self._cdb.ecdb.db._gmd, symbols=target_sym_names, eps_to_zero=False)
                gmd_list = target_sym_names
            else:
                dup_name_list = [
                    name
                    for name in target_sym_names
                    if write_container[name].hasDuplicateRecords()
                ]
                self._connect_error(
                    f"Following symbols have duplicate records: {dup_name_list}. Consider setting 'duplicateRecords' to 'first', 'last', or 'none'."
                )
        else:
            symbols_raw = self._symbols.copy()
            for s in self._symbols:
                self._update_sym_inst(s, self._inst)

            # Since we can't copy invalid symbols (=symbols with duplicates) we need to resolve the duplicates in the Connect container
            all_dr = any(sym["duplicateRecords"] != "all" for sym in self._symbols)
            if all_dr:
                # copy Connect container to avoid altering the Connect database
                write_container = gt.Container(
                    self._cdb.container, system_directory=self._system_directory
                )

            sym_names = []
            for sym, sym_raw in zip(self._symbols, symbols_raw):
                if self._trace > 0:
                    self._log_instructions(
                        sym, sym_raw, description=f"Write symbol >{sym['name']}<:"
                    )

                sym_name = sym["name"]
                self._symbols_exist_cdb(sym_name, should_exist=True)

                if sym["duplicateRecords"] != "all":
                    write_container[sym_name].dropDuplicateRecords(
                        keep=drmap[sym["duplicateRecords"]]
                    )
                if not write_container[sym_name].hasDuplicateRecords():
                    sym_names.append(sym_name)
                else:
                    self._connect_error(
                        f"Symbol '{sym_name}' has duplicate records. Consider setting 'duplicateRecords' to 'first', 'last', or 'none'."
                    )
            gms = gt.Container(system_directory=self._system_directory)
            gms.read(write_container, sym_names)

            # Apply original categories of * domains in new Container
            for sym_name in gms.listSymbols():
                ssym = write_container[sym_name]
                tsym = gms[sym_name]
                if ssym.records is None:
                    continue
                for d, tdl, sdl in zip(
                    tsym.domain, tsym.domain_labels, ssym.domain_labels
                ):
                    if isinstance(d, str):
                        tsym.records[tdl] = tsym.records[tdl].astype(
                            pd.CategoricalDtype(
                                categories=ssym.records[sdl].cat.categories,
                                ordered=True,
                            )
                        )

            # Renaming
            if self._trace > 1:
                self._cdb.print_log(f"GAMS symbols: {gms.listSymbols()}\n")
            for sym in self._symbols:
                if sym["newName"] is not None:
                    gms.renameSymbol(sym["name"], sym["newName"])

            if self._trace > 0:
                self._describe_container(gms, "GAMS Container:")
            if self._trace > 2:
                for name, sym in gms.data.items():
                    self._cdb.print_log(f"GAMS Container symbol={name}: {sym.records}")
            gms.write(self._cdb.ecdb.db._gmd, eps_to_zero=False)
            gmd_list = gms.listSymbols()

        # Build the modSymList with merge type and domain check type
        merge_type_lookup = {"replace": 0, "merge": 1, "default": 2}
        domain_check_type_lookup = {"filtered": 0, "checked": 1, "default": 2}
        rc = new_intp()
        self._cdb.ecdb._modSymList = {}
        for sym_name in gmd_list:
            sym_ptr = gmdFindSymbolPy(self._cdb.ecdb.db._gmd, sym_name, rc)
            if not intp_value(rc):
                self._connect_error(gmdGetLastError(self._cdb.ecdb.db._gmd)[1])
            ret = gmdSymbolInfo(self._cdb.ecdb.db._gmd, sym_ptr, GMD_NUMBER)
            if not ret[0]:
                self._connect_error(gmdGetLastError(self._cdb.ecdb.db._gmd)[1])
            if self._write_all:
                mt = self._merge_type
                dct = self._domain_check_type
            else:
                sym = sym_map[sym_name]
                mt = sym["mergeType"]
                dct = sym["domainCheckType"]
            self._cdb.ecdb._modSymList[ret[1]] = (
                merge_type_lookup[mt],
                domain_check_type_lookup[dct],
            )
        delete_intp(rc)
