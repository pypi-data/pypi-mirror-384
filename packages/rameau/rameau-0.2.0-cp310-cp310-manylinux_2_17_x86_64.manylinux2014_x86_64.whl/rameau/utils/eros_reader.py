# Copyright 2025, BRGM
# 
# This file is part of Rameau.
# 
# Rameau is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# Rameau is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# Rameau. If not, see <https://www.gnu.org/licenses/>.
#
import datetime
import re
import string
from warnings import warn

import numpy as np
import pandas as pd

import rameau.core as rm

def create_model_from_eros(path, encoding='latin-1'):
    """ Create a Rameau model from an Eros project file (v7.3)

    Parameters
    ----------
    path : str or Path
        Path to the Eros project file.
    encoding : str, optional
        encoding of the eros file, by default 'latin-1'

    Returns
    -------
    rameau.core.Model
        A Rameau model object containing the parsed data from the Eros project file.
    """
    eros = ErosReader()
    files = eros.read_project(path, encoding=encoding)
    df = eros.read_arbros(files["arbros"], encoding=encoding)
    con = {row.iloc[0]:row.iloc[2] for _, row in df.iterrows()}
    is_c = {row.iloc[0]:row.iloc[3] for _, row in df.iterrows()}
    name = {row.iloc[0]:row.iloc[-1] for _, row in df.iterrows()}
    gw_pump = {row.iloc[0]:row.iloc[-2] for _, row in df.iterrows()}
    riv_pump = {row.iloc[0]:row.iloc[-3] for _, row in df.iterrows()}
    files2 = rm.FilePaths(
        rainfall=files["rainfall"],
        pet=files["pet"],
        temperature=files["temperature"],
        snow=files["snow"],
        riverobs=files["riverobs"],
        riverpumping=files["riverpumping"],
        groundwaterobs=files["groundwaterobs"],
    )
    opt_opts, sim_opts, input_format, watersheds = eros.read_parameter(
        files["ros"], gw_pump, riv_pump, encoding=encoding
    )
    
    inputs = rm.inputs.InputCollection.from_files(
        rainfall=files2.rainfall,
        pet=files2.pet,
        temperature=files2.temperature,
        snow=files2.snow,
        riverobs=files2.riverobs,
        riverpumping=files2.riverpumping,
        groundwaterobs=files2.groundwaterobs,
        input_format=input_format
    )
    for key, value in is_c.items():
        watersheds[key - 1].is_confluence = bool(value)
    for key, value in name.items():
        watersheds[key - 1].name = value
    
    tree = rm.Tree(
        watersheds=watersheds,
        connection=con
    )

    # only after watersheds id is init in tree, parse meteo weight 
    if files.get("meteo_weights", '') != '':
        meteo_weights = eros.parse_meteo_weight(
            files["meteo_weights"],
            basin_id=df['Num_Ord'].to_list() if 'Num_Ord' in df.columns else None
        )
        for i in range(len(watersheds)):
            weight = meteo_weights.get(f'watershed.{tree.watersheds[i].id}')
            if weight is None:
                continue
            tree.watersheds[i].meteo.columns = weight.get('meteo.columns', [1])
            tree.watersheds[i].meteo.weights = weight.get('meteo.weights', [1.0])

    model = rm.Model(
        tree=tree,
        inputs=inputs,
        simulation_settings=sim_opts,
        optimization_settings=opt_opts
    )

    return model

def scan_version_proj(line):
    res = re.findall("#<V(.*)>#", line)
    if res:
        return get_version(res[0])
    return 700

def scan_version(line):
    res = re.findall("#<V(.*)>#", line)
    if res:
        return get_version(res[0])
    return snif_version(line)

def get_version(release):
    release = release.replace(".", "")
    if len(release) >= 3:
        subvers = string.ascii_lowercase.index(release[-1])
        release = release[:2] + str(subvers + 1)
    else:
        release = release + '0'
    release = int(release)
    return release

def snif_version(line):
    starSeps = re.findall('\n *' + re.escape("***") + ".*", line)
    texts = []
    for i in range(len(starSeps)):
        if i == 0:
            istart = 0
        else:
            istart = re.search(re.escape(starSeps[i-1]), lines).end()
        lines = lines[istart:]
        iend = re.search(re.escape(starSeps[i]), lines).start()
        text = lines[:iend].strip().split('\n')
        if text != ['']:
            texts.append(text)
    if len(texts[5]) == 9:
        if len(texts[8]) == 12:
            return 650
        else:
            return 600
    return 300

def left_float_equal(line):
    return float(line.split("=")[0])

def left_int_equal(line):
    return int(line.split("=")[0])

def left_str_equal(line):
    return str(line.split("=")[0].strip())

def left_bool_equal(line):
    n = int(line.split("=")[0])
    if n == 0:
        return False
    else:
        return True

def float_minmax(line):
    min, max = re.findall("(.*)=Min.*Max =(.*)$", line)[0]
    return float(min.strip()), float(max.strip())

def float_opt(line):
    min, opt = re.findall("([^=]*)=.*Opti=(.*)$", line)[0]
    if int(opt.strip()) == 0:
        opt = False
    else:
        opt = True
    return float(min.strip()), opt

def float_opt_mem(line):
    min, opt, mem = re.findall("([^=]*)=.*Opti=(.*)Même_Que=(.*)$", line)[0]
    if int(opt.strip()) == 0:
        opt = False
    else:
        opt = True
    return float(min.strip()), opt, int(mem.strip())

class ErosReader():
    def read_project(self, filename, encoding='latin-1'):
        files = {}
        with open(filename, 'r', encoding=encoding) as f:
            for line in f:
                if "Fin du texte libre" in line:
                    break
            f.readline() # Nom générique 
            files["arbros"] = left_str_equal(f.readline())
            files["ros"] = left_str_equal(f.readline()) # ros paramètre
            files["rainfall"] = left_str_equal(f.readline())
            files["pet"] = left_str_equal(f.readline())
            files["riverobs"] = left_str_equal(f.readline())
            files["groundwaterobs"] = left_str_equal(f.readline())
            files["temperature"] = left_str_equal(f.readline())
            files["snow"] = left_str_equal(f.readline())
            files["forecast_rainfall"] = left_str_equal(f.readline())
            files["forecast_pet"] = left_str_equal(f.readline())
            files["forecast_temperature"]= left_str_equal(f.readline())
            files["forecast_snow"] = left_str_equal(f.readline())
            files["riverpumping"] = left_str_equal(f.readline())
            f.readline() # Etat du réservoir sol progressif
            f.readline() # Applications d'engrais
            f.readline() # Besoins en NO3 des cultures
            f.readline() # Résidus en NO3 après récolte
            f.readline() # Minéralisation du sol
            f.readline() # Concentration en NO3 dans les rivières
            f.readline() # Concentration en NO3 dans les nappes
            files['meteo_weights'] = f.readline().split('=')[0].strip()  # Mailles mmétéo et pondération
            f.readline() # Etats initiaux
            f.readline() # Pourcentages de Cultures
        return files

    def read_arbros(self, filename, encoding='latin-1'):
        with open(filename, 'r', encoding=encoding) as f:
            for line in f:
                if "Fin du texte libre" in line:
                    break
            header = f.readline().split()[1:]
            df = pd.read_csv(
                f,
                skipfooter=1,
                engine='python',
                sep='\s+',
                header=None
            )
            df.columns = header
        return df
    
    def read_parameter(self, filename, gw_pump, riv_pump, encoding='latin-1'):
        optimization = {}
        simulation_settings = {}
        spinup_settings = {}
        input_format = {}
        with open(filename, 'r', encoding=encoding) as f:
            for line in f:
                if "Fin du texte libre" in line:
                    version = scan_version(line)
                    break
            f.readline() # *** Paramètres généraux
            nyear = left_int_equal(f.readline())
            hydro = left_int_equal(f.readline())
            fyear = left_int_equal(f.readline())
            start = left_int_equal(f.readline())
            spinup_settings["cycles"] = left_int_equal(f.readline())
            if spinup_settings["cycles"] == 0:
                spinup_settings["cycles"] = 1
            final = left_int_equal(f.readline())
            f.readline() # Dessin
            weight_riv = left_int_equal(f.readline())
            weight_gw = left_int_equal(f.readline())
            f.readline() # Calcul des débits
            f.readline() # Calcul des niveaux de nappe
            dt = left_int_equal(f.readline()) # Pas de temps des données
            f.readline() # Format des données
            f.readline() # Schéma de calcul
            pet_decrease = left_bool_equal(f.readline())
            f.readline() # Schéma à taux de ruissellement constant
            f.readline() # Schéma d'échange souterrain extérieur
            f.readline() # Prise en compte de la neige
            f.readline() # Précipitaiton neigeuses dans un fichier
            #warnings.warn("Skip all parameters related to forecast.", Warning)
            f.readline() # Nombre d'années de données pour la prévi
            f.readline() # Date de la première année
            f.readline() # Prévision
            f.readline() # Méthode de correction des écarts de prévi
            f.readline() # Jour de prévi
            f.readline() # Mois (ou pdt) de prévi
            if version == 735:
                f.readline() # Heure d'émission
                f.readline() # Numéro de l'année utilisée pour les pompages pendant la prévision
            f.readline() # Portée de prévi
            f.readline() # Taux de réajustement
            f.readline() # *** Durée du pas de temps
            unit = left_str_equal(f.readline())
            step = left_float_equal(f.readline())
            day = left_int_equal(f.readline())
            month = left_int_equal(f.readline())
            hour = left_int_equal(f.readline())
            minute = left_int_equal(f.readline())

            # deduce dates from user provided time information
            if (
                    (dt == 4) and (unit != 'Standard')
                    and (fyear != 0) and (month != 0) and (day !=0)
            ):
                input_format["starting_date"] = datetime.datetime(
                    fyear, month, day, hour, minute
                )
                label = (
                    'seconds' if unit.startswith("sec")
                    else 'minutes' if unit.startswith("min")
                    else 'hours' if unit.startswith("heu")
                    else 'days'
                )
            else:
                label, step = (
                    ('days', 1) if dt == 0
                    else ('hours', 1) if dt == 24
                    else ('days', 10) if dt == 2
                    else ('days', 30.4) if dt == 3
                    else ('days', 5) if dt == 5
                    else ('days', 7) if dt == 7
                    else ('days', 1)
                )

            if (label == 'days') and (step == 30.4):
                warn('monthly time step converted to time delta of 30.4 days,'
                     'output date and time may be slightly off as a result')

            time_step = datetime.timedelta(
                **{label:step if step > 0 else 1}
            )

            input_format["time_step"] = time_step

            starting_date = datetime.datetime(
                fyear + start, 8 if hydro else 1, 1
            )
            optimization["starting_date"] = starting_date
            simulation_settings["starting_date"] = starting_date

            spinup_settings["ending_date"] = starting_date - time_step

            if final < 0:
                # last year number if negative
                optimization["ending_date"] = (
                    datetime.datetime(
                        -final, 8 if hydro else 1, 1
                    ) - time_step
                )
            else:
                if nyear != 0:
                    # no info for starting date if nyear == 0
                    optimization["ending_date"] = (
                        datetime.datetime(
                            fyear + nyear - final, 8 if hydro else 1, 1
                        ) - time_step
                    )

            f.readline() # *** Paramètres généraux de la simulation
            f.readline() # Sauvegarde de la pluie efficace
            f.readline() # Sauvegarde des débits
            f.readline() # Sauvegarde des débits
            f.readline() # Ecriture sur listing
            f.readline() # Dessin
            f.readline() # Ecriture de contrôle
            f.readline() # Génération d'un listing
            tran = left_int_equal(f.readline()) # Transformation du débit
            if tran == 97:
                tran = "log"
            elif tran == 99:
                tran = "square root"
            else:
                tran = "no"
            optimization["transformation"] = tran
            f.readline() # minmisation du biais sur les débits
            optimization["maxit"] = left_int_equal(f.readline())
            f.readline() # Nombre de cycles de calibration
            f.readline() # Schéma de calibration
            f.readline() # Sauvegarde des termes du bilan global
            f.readline() # Numéro du bassin dont on sauvegarde les termes du bilan
            f.readline() # Sauvegarde des composantes de débit
            f.readline() # Bassins versants tous indépendants
            f.readline() # Sauvegarde des débits locaux
            meteo_files = int(f.readline().split("=")[0])
            if meteo_files in [0, 2]:
                input_format["meteo_files"] = False
            else:
                input_format["meteo_files"] = True
            f.readline() # Sauvegarde de la météo pondérée
            f.readline() # Couplage avec le coupleur openpalm
            f.readline() # Restart à partir des états de réservoirs

            line = f.readline() # ** Paramètres généraux pour le transfert de Nitrates
            for _ in range(12):
                f.readline()

            f.readline() # *** Bornes des paramètres hydroclimatiques
            min, maxi = float_minmax(f.readline())
            correction_rainfall = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            correction_pet = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            thorn_cap = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            prog_cap = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            runsee = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            halflife = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            gw1_baseflow = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            gw1_drainage = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            gw1_overflow_threshold = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            gw2_baseflow = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            concentration = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            gw1_exchanges = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            propagation = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            transfer_overflow_threshold = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            transfer_overflow_halflife = dict(lower=min, upper=maxi)
            f.readline() # Temps de demi décroissance maximal du ruissellement
            min, maxi = float_minmax(f.readline())
            correction_area = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            storage_coeff = dict(lower=min, upper=maxi)

            f.readline() # *** Bornes des paramètres de fonte de neige
            min, maxi = float_minmax(f.readline())
            snow_temperature = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            retention = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            snow_pet = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            snow_rainfall = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            degreeday_temperature = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            degreeday_coefficient = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            melting = dict(lower=min, upper=maxi)

            f.readline() # ***  Bornes des paramètres de pompage
            min, maxi = float_minmax(f.readline())
            river_rise = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            river_fall = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            groundwater_rise = dict(lower=min, upper=maxi)
            min, maxi = float_minmax(f.readline())
            groundwater_fall = dict(lower=min, upper=maxi)
            for _ in range(21): # On saute les nitrates
                f.readline()

            watersheds = []
            ibas = 1
            while True:
                line = f.readline() # *** Options hydroclimatiques ...
                if "Fin du fichier" in line:
                    break
                nres = left_int_equal(f.readline())
                watertable = left_int_equal(f.readline())
                if watertable == 0:
                    watertable = 1
                loss = left_int_equal(f.readline())
                if loss == 0:
                    loss = "no"
                elif loss == 1:
                    loss = "loss"
                elif loss == 2:
                    loss = "groundwater"
                regression = left_int_equal(f.readline())
                if regression == 0:
                    regression = True
                else:
                    regression = False
                f.readline() # ***  Paramètres hydroclimatique
                f.readline() # Pluie efficace
                val = left_float_equal(f.readline())
                minimum = dict(value=val)
                f.readline() # Temps de demi-vie prév débit
                f.readline() # Temps de demi-vie prév nappe
                val, opt = float_opt(f.readline())
                area = dict(value=val, opti=opt)
                val, opt = float_opt(f.readline())
                base_level = dict(value=val, opti=opt)
                val, opt, _ = float_opt_mem(f.readline())
                correction_rainfall.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                correction_pet.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                thorn_cap.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                prog_cap.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                runsee.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                halflife.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                gw1_baseflow.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                gw1_drainage.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                gw1_overflow_threshold.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                gw2_baseflow.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                concentration.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                gw1_exchanges.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                propagation.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                transfer_overflow_threshold.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                transfer_overflow_halflife.update(dict(value=val, opti=opt))
                f.readline() # Temps de demi-ruissellement maximum
                val, opt, _ = float_opt_mem(f.readline())
                correction_area.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                storage_coeff.update(dict(value=val, opti=opt))
                f.readline() # *** Paramètres de fonte de la neige
                val, opt, _ = float_opt_mem(f.readline())
                snow_temperature.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                retention.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                snow_pet.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                snow_rainfall.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                degreeday_temperature.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                degreeday_coefficient.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                melting.update(dict(value=val, opti=opt))
                f.readline() # *** Paramètres de pompage
                val, opt = float_opt(f.readline())
                if (riv_pump[ibas] > 0):
                    river_coefficient = dict(value=1, opti=opt)
                else:
                    river_coefficient = dict(value=0, opti=opt)
                val, opt, _ = float_opt_mem(f.readline())
                river_rise.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                river_fall.update(dict(value=val, opti=opt))
                val, opt = float_opt(f.readline())
                if (gw_pump[ibas] > 0):
                    groundwater_coefficient = dict(value=1, opti=opt)
                else:
                    groundwater_coefficient = dict(value=0, opti=opt)
                groundwater_coefficient = dict(value=val, opti=opt)
                val, opt, _ = float_opt_mem(f.readline())
                groundwater_rise.update(dict(value=val, opti=opt))
                val, opt, _ = float_opt_mem(f.readline())
                groundwater_fall.update(dict(value=val, opti=opt))
                for _ in range(26):
                    line = f.readline()
                correction = rm.CorrectionParameters(
                    area=correction_area,
                    rainfall=correction_rainfall,
                    pet=correction_pet
                )
                thorn = rm.ThornthwaiteReservoir(
                    capacity=thorn_cap
                )
                prog = rm.ProgressiveReservoir(
                    capacity=prog_cap,
                    pet_decrease=pet_decrease
                )
                transfer = rm.TransferReservoir(
                    runsee=runsee,
                    halflife=halflife,
                    overflow=rm.OverflowParameters(
                        threshold=transfer_overflow_threshold,
                        halflife=transfer_overflow_halflife,
                        loss=loss
                    )
                )

                gw1 = rm.groundwater.GroundwaterReservoir(
                    halflife_baseflow=(
                        gw1_baseflow if nres in [1, 2]
                        else gw2_baseflow
                    ),
                    halflife_drainage=(
                        gw1_drainage if nres == 2
                        else dict(
                            value=0, opti=False,
                            lower=gw1_drainage['lower'],
                            upper=gw1_drainage['upper']
                        )
                    ),
                    exchanges=gw1_exchanges,
                    overflow=rm.OverflowParameters(
                        threshold=gw1_overflow_threshold,
                        halflife=(
                            gw1_baseflow if nres == -1
                            else dict(
                                value=0, opti=False,
                                lower=gw1_baseflow['lower'],
                                upper=gw1_baseflow['upper']
                            )
                        )
                    )
                )
                gw2 = rm.groundwater.GroundwaterReservoir(
                    halflife_baseflow=(
                        gw2_baseflow if nres == 2
                        else dict(
                            value=0, opti=False,
                            lower=gw2_baseflow['lower'],
                            upper=gw2_baseflow['upper']
                        )
                    ),
                )
                gw = rm.groundwater.GroundwaterParameters(
                    weight=weight_gw,
                    reservoirs=[gw1, gw2],
                    base_level=base_level,
                    observed_reservoir=watertable,
                    storage=rm.groundwater.StorageParameters(
                        coefficient=storage_coeff,
                        regression=regression
                    )
                )
                river = rm.RiverParameters(
                    area=area,
                    exchange_riverflow=minimum,
                    concentration_time=concentration,
                    propagation_time=propagation,
                    weight=weight_riv
                )
                snow = rm.snow.SnowReservoir(
                    retention=retention,
                    melting=melting,
                    degree_day=rm.snow.DegreeDayParameters(
                        coefficient=degreeday_coefficient,
                        temperature=degreeday_temperature
                    ),
                    snow_correction=rm.snow.SnowCorrectionParameters(
                        rainfall=snow_rainfall,
                        pet=snow_pet,
                        temperature=snow_temperature
                    )
                )
                pumping = rm.pumping.Pumping(
                    river=rm.pumping.PumpingReservoir(
                        coefficient=river_coefficient,
                        halflife_fall=river_fall,
                        halflife_rise=river_rise
                    ),
                    groundwater=rm.pumping.PumpingReservoir(
                        coefficient=groundwater_coefficient,
                        halflife_fall=groundwater_fall,
                        halflife_rise=groundwater_rise
                    ),
                )
                watershed = rm.Watershed(
                    river=river,
                    correction=correction,
                    thornthwaite_reservoir=thorn,
                    progressive_reservoir=prog,
                    transfer_reservoir=transfer,
                    snow_reservoir=snow,
                    pumping=pumping,
                    groundwater=gw,
                )
                watersheds.append(watershed)
        optimization = rm.settings.OptimizationSettings(**optimization)
        input_format = rm.inputs.InputFormat(**input_format)
        simulation_settings["spinup_settings"] = rm.settings.SpinupSettings(**spinup_settings)
        simulation_settings = rm.settings.SimulationSettings(**simulation_settings)
        return optimization, simulation_settings, input_format, watersheds
        
    @staticmethod
    def parse_meteo_weight(fname, basin_id=None):
        """ Parse a meteorological weight file and return a dictionary
        with watershed names as keys and their corresponding meteorological
        columns and weights as values.

        Parameters
        ----------
        fname : str
            Path to the meteorological weight file.
        
        basin_id : list or None, optional
            List of basin IDs to create output keys. If None, use a range from 1 to N,
            N being the number of basin found in weight file.

        Returns
        -------
        dict
            A dictionary where keys are watershed names and values are dictionaries
            containing 'meteo.columns' and 'meteo.weights' as keys with their respective
            values as lists of integers and floats, respectively.
        """

        with open(fname, 'r', encoding='ISO-8859-1') as f:
            lines = f.readlines()
        
        idx_grp = [i for i, line in enumerate(lines) if re.match(r'^Num(?:éro)?_Maille.*', line.strip())]
        idx_grp.append(len(lines))  # Add the end of the file as a split point
        
        meteo_weight = {}
        for i in range(len(idx_grp) - 1):
            start = idx_grp[i] + 1
            end = idx_grp[i + 1]
            group_lines = lines[start:end]
            group_data = [line.strip().split() for line in group_lines if line.strip()]
            group_data = np.array(group_data, dtype=float)
            
            watershed_id = basin_id[i] if basin_id is not None else i + 1
            meteo_weight['watershed.{}'.format(watershed_id)] = {
                'meteo.columns': group_data[:, 0].astype(int).tolist(),
                'meteo.weights': group_data[:, 1].astype(float).tolist()
            }
        
        return meteo_weight
    