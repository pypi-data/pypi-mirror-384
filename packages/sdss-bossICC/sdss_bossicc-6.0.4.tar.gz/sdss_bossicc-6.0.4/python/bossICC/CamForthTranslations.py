voltage_translations = {
    "R0_LN2TEMP": ("R0", "LN2Temp", 1, 0, 200, 315),
    "R0_HEATERV": None,
    "R0_CCDTEMP": ("R0", "CCDTemp", 1, 0, 200, 512),
    "R0_TSET": ("R0", "TSet", -200, 0, -200, 253),
    "R0_TZERO": ("R0", "TZero", -17, 128, -17, 512),
    "R0_I-TRIM2": ("R0", "INegTrim2", 10, 128, 10, 512),
    "R0_I-TRIM1": ("R0", "INegTrim1", 10, 128, 10, 512),
    "R0_I+TRIM2": ("R0", "IPosTrim2", 10, 128, 10, 512),
    "R0_I+TRIM1": ("R0", "IPosTrim1", 10, 128, 10, 512),
    "R0_VSW-": ("R0", "VSWb", -10, 256, -10, 512),
    "R0_VLG": ("R0", "VLG1", -5, 256, -5, 512),
    "R0_VT-": ("R0", "VTc", 10, 256, 10, 512),
    "R0_VT+": ("R0", "VTb", 10, 0, 10, 512),
    "R0_VP3-": ("R0", "VPcB", 10, 256, 10, 512),
    "R0_VP12-": ("R0", "VPcA", 10, 256, 10, 512),
    "R0_VP3+": ("R0", "VPbB", 10, 0, 10, 512),
    "R0_VP12+": ("R0", "VPbA", 10, 0, 10, 512),
    "R0_VS-": ("R0", "VSb1", -10, 256, -10, 512),
    "R0_VS+": ("R0", "VSc1", -10, 0, -10, 512),
    "R0_VR": None,
    "R0_VRD2": ("R0", "VRD2", -16, 0, -20, 512),
    "R0_VRD1": ("R0", "VRD1", -16, 0, -20, 512),
    "R0_VDD2": ("R0", "VDD2", -26, 0, -30, 512),
    "R0_VDD1": ("R0", "VDD1", -26, 0, -30, 512),
    "R1_LN2TEMP": None,
    "R1_HEATERV": ("R1", "HeaterV", 10, 0, 10, 512),
    "R1_CCDTEMP": None,
    "R1_TSET": None,
    "R1_TZERO": None,
    "R1_I-TRIM2": ("R1", "INegTrim4", 10, 128, 10, 512),
    "R1_I-TRIM1": ("R1", "INegTrim3", 10, 128, 10, 512),
    "R1_I+TRIM2": ("R1", "IPosTrim4", 10, 128, 10, 512),
    "R1_I+TRIM1": ("R1", "IPosTrim3", 10, 128, 10, 512),
    "R1_VSW-": ("R1", "VRon", 10, 256, 10, 512),
    "R1_VLG": ("R1", "VLG2", -5, 256, -5, 512),
    "R1_VT-": ("R1", "VLG3", -5, 256, -5, 512),
    "R1_VT+": ("R1", "VLG4", 5, 0, 5, 512),
    "R1_VP3-": ("R1", "VRedPurge", 10, 256, 10, 512),
    "R1_VP12-": ("R1", "VPcC", 10, 256, 10, 512),
    "R1_VP3+": ("R1", "VRedErase", 10, 0, 10, 512),
    "R1_VP12+": ("R1", "VPbC", 10, 0, 10, 512),
    "R1_VS-": ("R1", "VSb2", -10, 256, -10, 512),
    "R1_VS+": ("R1", "VSc2", -10, 0, -10, 512),
    "R1_VR": ("R1", "VSubs", -91, 256, 125, 512),
    "R1_VRD2": ("R1", "VRD4", -16, 0, -20, 512),
    "R1_VRD1": ("R1", "VRD3", -16, 0, -20, 512),
    "R1_VDD2": ("R1", "VDD4", -26, 0, -30, 512),
    "R1_VDD1": ("R1", "VDD3", -26, 0, -30, 512),
    "B2_LN2TEMP": ("B2", "LN2Temp", 1, 0, 200, 315),
    "B2_HEATERV": None,
    "B2_CCDTEMP": ("B2", "CCDTemp", 1, 0, 200, 512),
    "B2_TSET": ("B2", "TSet", -200, 0, -200, 523),
    "B2_TZERO": ("B2", "TZero", -17, 128, -17, 512),
    "B2_I-TRIM2": ("B2", "INegTrim2", 10, 128, 10, 512),
    "B2_I-TRIM1": ("B2", "INegTrim1", 10, 128, 10, 512),
    "B2_I+TRIM2": ("B2", "IPosTrim2", 10, 128, 10, 512),
    "B2_I+TRIM1": ("B2", "IPosTrim1", 10, 128, 10, 512),
    "B2_VSW-": ("B2", "VSWb", 10, 256, 10, 512),
    "B2_VLG": ("B2", "VLG12", 5, 256, 5, 512),
    "B2_VT-": ("B2", "VTb", 10, 256, 10, 512),
    "B2_VT+": ("B2", "VTc", 10, 0, 10, 512),
    "B2_VP3-": ("B2", "VPbB", 10, 256, 10, 512),
    "B2_VP12-": ("B2", "VPbA", 10, 256, 10, 512),
    "B2_VP3+": ("B2", "VPcB", 10, 0, 10, 512),
    "B2_VP12+": ("B2", "VPcA", 10, 0, 10, 512),
    "B2_VS-": ("B2", "VSb1", 10, 256, 10, 512),
    "B2_VS+": ("B2", "VSc1", 10, 0, 10, 512),
    "B2_VR": ("B2", "VRon", -15, 256, 20, 512),
    "B2_VRD2": ("B2", "VRD2", 16, 0, 20, 512),
    "B2_VRD1": ("B2", "VRD1", 16, 0, 20, 512),
    "B2_VDD2": ("B2", "VDD2", 26, 0, 30, 512),
    "B2_VDD1": ("B2", "VDD1", 26, 0, 30, 512),
    "B3_LN2TEMP": None,
    "B3_HEATERV": ("B3", "HeaterV", 10, 0, 10, 512),
    "B3_CCDTEMP": None,
    "B3_TSET": None,
    "B3_TZERO": None,
    "B3_I-TRIM2": ("B3", "INegTrim4", 10, 128, 10, 512),
    "B3_I-TRIM1": ("B3", "INegTrim3", 10, 128, 10, 512),
    "B3_I+TRIM2": ("B3", "IPosTrim4", 10, 128, 10, 512),
    "B3_I+TRIM1": ("B3", "IPosTrim3", 10, 128, 10, 512),
    "B3_VSW-": ("B3", "VRoff", 10, 256, 10, 512),
    "B3_VLG": ("B3", "VLG34", 5, 256, 5, 512),
    "B3_VT-": None,
    "B3_VT+": None,
    "B3_VP3-": ("B3", "VPbD", 10, 256, 10, 512),
    "B3_VP12-": ("B3", "VPbC", 10, 256, 10, 512),
    "B3_VP3+": ("B3", "VPcD", 10, 0, 10, 512),
    "B3_VP12+": ("B3", "VPcC", 10, 0, 10, 512),
    "B3_VS-": ("B3", "VSb2", 10, 256, 10, 512),
    "B3_VS+": ("B3", "VSc2", 10, 0, 10, 512),
    "B3_VR": None,
    "B3_VRD2": ("B3", "VRD4", 16, 0, 20, 512),
    "B3_VRD1": ("B3", "VRD3", 16, 0, 20, 512),
    "B3_VDD2": ("B3", "VDD4", 26, 0, 30, 512),
    "B3_VDD1": ("B3", "VDD3", 26, 0, 30, 512),
}

keyword_translations = {
    "LN2_FILL": "LN2Fill",
    "CAMERA_MONITOR": "CameraMonitor",
    "E0": "Cam0",
    "E1": "Cam1",
    "E2": "Cam2",
    "E3": "Cam3",
    "SERIAL_BIN": "SerialBin",
    "SERIAL_DIR": "SerialDir",
    "PARALLEL_BIN": "ParallelBin",
    "SERIAL_SPEED": "SerialSpeed",
    "PIXELS": "Pixels",
    "BINNED_PIXELS": "BinnedPixels",
    "BLUE_PARALLEL_DIR": "BlueParallelDir",
    "BLUE_PARALLEL_STATE": "BlueParallelState",
    "RED_PARALLEL_DIR": "RedParallelDir",
    "RED_PARALLEL_STATE": "RedParallelState",
    "DATA_MODE": "DataMode",
    "LINES": "Lines",
    "BINNED_LINES": "BinnedLines",
    "DATA_STATE": "DataState",
    "LINESTART": "Linestart",
    "LINESTART_PERIOD": "LinestartPeriod",
    "DACS_SET": "DacsSet",
    "EXEC_BOOT": "ExecBoot",
    "PHASE_BOOT": "PhaseBoot",
    "USR1": "USR1",
    "USR2": "USR2",
    "USR3": "USR3",
    "LN2_EMPTY": "LN2Empty",
    "2NDARY_DEWAR_PRESS": "SecondaryDewarPress",
    "LN2TEMP": "LN2Temp",
    "CCDTEMP": "CCDTemp",
    "TSET": "TSet",
    "TZERO": "TZero",
    "FILLTIME": "FillTime",
    "NEXT_FILL": "NextFill",
    "NORM_RETRIG": "NormRetrig",
    "WARM_FILLTIME": "WarmFillTime",
    "WARM_FILLS": "WarmFills",
    "WARM_RETRIG": "WarmRetrig",
    "FILLFAULT": "FillFault",
    "EMPTY_TRIGGER": "EmptyTrigger",
    "2NDLN2_FILL": "SecondLN2Fill",
    "RED_ION_PUMP_LOGP": "RedIonPump",
    "BLU_ION_PUMP_LOGP": "BlueIonPump",
}
if __name__ == "__main__":
    output = open("gen_dictionary", "w")
    doubles = []
    count = 0

    # From sigbias_translation_all.txt
    # The voltages LN2TEMP, HEATERV, and CCDTEMP are monitored only
    # and have no 8-bit DAC setting, since they are not `set'.
    skipbias = ("CCDTemp", "LN2Temp", "HeaterV")

    for key, value in list(voltage_translations.items()):
        if not value:
            continue
        for spec in ("SP1", "SP2"):
            for kind in ("Bias", "Nom", "Read"):
                board = value[0]
                boss_name = value[1]

                if boss_name in skipbias:
                    if kind == "Bias":
                        continue

                count += 1
                boss_key_name = "%s%s%s%s" % (spec, board, boss_name, kind)
                if boss_key_name not in doubles:
                    doubles.append(boss_key_name)
                else:
                    print("Variable already used.", boss_key_name)
                    continue

                if key.endswith("CCDTEMP"):
                    units = "deg C"
                elif key.endswith("LN2TEMP"):
                    units = "deg K"
                else:
                    units = "volts"

                entry = """
                    Key('%s',
                        Float(units='%s',strFmt='%s'),
                        help = "Translated value of %s on %s %s"
                    ),""" % (
                    boss_key_name,
                    units,
                    "%.3f",
                    key,
                    spec,
                    board,
                )
                print(entry)
                output.write(entry)
    print(count)
    output.close()
