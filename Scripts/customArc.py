#!/usr/bin/python

# Copyright 2015 Seth VanHeulen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import os
import struct
import zlib


file_types = [
    # Monster Hunter 4 Ultimate file types
    ['rArchive', 'arc'],
    ['rCameraList', 'lcm'],
    ['rChainCol', 'ccl'],
    ['rCnsTinyChain', 'ctc'],
    ['rCollision', 'sbc'],
    ['rEffectAnim', 'ean'],
    ['rEffectList', 'efl'],
    ['rEnemyCmd', 'emc'],
    ['rEnemyData', 'emd'],
    ['rEnemyTuneData', 'etd'],
    ['rEventActorTbl', 'evt'],
    ['rGrass2', 'gr2'],
    ['rGrass2Setting', 'gr2s'],
    ['rGrassWind', 'grw'],
    ['rItemPopList', 'ipl'],
    ['rItemPopSet', 'ips'],
    ['rLayout', 'lyt'],
    ['rLayoutAnimeList', 'lanl'],
    ['rLayoutFont', 'lfd'],
    ['rLayoutMessage', 'lmd'],
    ['rLtProceduralTexture', 'ptex'],
    ['rLtShader', 'lfx'],
    ['rLtSoundBank', 'sbk'],
    ['rLtSoundCategoryFilter', 'cfl'],
    ['rLtSoundRequest', 'srq'],
    ['rLtSoundReverb', 'rev_ctr'],
    ['rLtSoundSourceADPCM', 'mca'],
    ['rLtSoundStreamRequest', 'stq'],
    ['rMHSoundEmitter', 'ses'],
    ['rMHSoundSequence', 'mss'],
    ['rMaterial', 'mrl'],
    ['rMhMotionEffect', 'mef'],
    ['rModel', 'mod'],
    ['rMotionList', 'lmt'],
    ['rMovieOnDisk', 'moflex'],
    ['rQuestData', 'mib'],
    ['rScheduler', 'sdl'],
    ['rSoundAttributeSe', 'ase'],
    ['rSoundCurveSet', 'scs'],
    ['rSoundDirectionalSet', 'sds'],
    ['rStageAreaInfo', 'sai'],
    ['rStageCameraData', 'scd'],
    ['rStageInfoSet', 'sis'],
    ['rSwkbdMessageStyleTable', 'skst'],
    ['rSwkbdMessageTable', 'skmt'],
    ['rSwkbdSubGroup', 'sksg'],
    ['rTexture', 'tex'],
    # Monster Hunter X demo file types
    ['rAIWayPoint', 'way'],
    ['rActivityData', 'atd'],
    ['rAmuletData', 'amlt'],
    ['rAmuletSkillData', 'amskl'],
    ['rAmuletSlotData', 'amslt'],
    ['rAngryParam', 'angryprm'],
    ['rAreaActTblData', 'areaacttbl'],
    ['rAreaCommonLink', 'areacmnlink'],
    ['rAreaEatData', 'areaeatdat'],
    ['rAreaInfo', 'areainfo'],
    ['rAreaLinkData', 'arealinkdat'],
    ['rAreaPatrolData', 'areapatrol'],
    ['rAreaSelectData', 'areaseldat'],
    ['rArmorBuildData', 'abd'],
    ['rArmorColorData', 'acd'],
    ['rArmorResistData', 'ard'],
    ['rArmorSeData', 'ased'],
    ['rArmorSeriesData', 'asd'],
    ['rBodyData', 'bdd'],
    ['rBowgunShellData', 'bgsd'],
    ['rCommonScript', 'cms'],
    ['rDecoData', 'deco'],
    ['rEmDouMouKaData', 'mdd'],
    ['rEmSetList', 'esl'],
    ['rEmSizeCalcTblElement', 'emsizetbl'],
    ['rEmSizeYureTbl', 'emyure'],
    ['rEnemyDtBase', 'dtb'],
    ['rEnemyDtBaseParts', 'dtp'],
    ['rEnemyDtTune', 'dtt'],
    ['rEnemyNandoData', 'nan'],
    ['rEnemyResidentDtBase', 'rdb'],
    ['rEquipBaseColorData', 'ebcd'],
    ['rFestaPelTiedSe', 'pts'],
    ['rFestaResourceList', 'frl'],
    ['rFestaSoundEmitter', 'ses'],
    ['rFestaSoundSequence', 'mss'],
    ['rFishData', 'fsh'],
    ['rFreeUseParam', 'fup'],
    ['rFueMusicData', 'fmt'],
    ['rFueMusicInfData', 'fmi'],
    ['rFueMusicScData', 'fms'],
    ['rGUI', 'gui'],
    ['rGUIFont', 'gfd'],
    ['rGUIIconInfo', 'gii'],
    ['rGUIMessage', 'gmd'],
    ['rHagi', 'hgi'],
    ['rHitDataEnemy', 'hde'],
    ['rHitDataPlayer', 'hdp'],
    ['rHitDataShell', 'hds'],
    ['rHitSize', 'hts'],
    ['rHunterArtsData', 'hta'],
    ['rInsectAbirity', 'insectabirity'],
    ['rInsectAttr', 'isa'],
    ['rInsectData', 'isd'],
    ['rInsectEssenceSkill', 'insectessenceskill'],
    ['rInsectLevel', 'isl'],
    ['rInsectParam', 'isp'],
    ['rItemData', 'itm'],
    ['rItemPreData', 'itp'],
    ['rItemPreTypeData', 'ipt'],
    ['rKireajiData', 'kad'],
    ['rKowareObjData', 'kod'],
    ['rLayoutAnime', 'lan'],
    ['rMapTimeData', 'maptime'],
    ['rMonsterPartsManager', 'mpm'],
    ['rOtArmorData', 'oar'],
    ['rOtLevel', 'olvl'],
    ['rOtMessageLot', 'otml'],
    ['rOtQuestExpBias', 'oxpb'],
    ['rOtQuestExpValue', 'oxpv'],
    ['rOtSkill', 'oskl'],
    ['rOtSpecialAction', 'osa'],
    ['rOtSupportActionBase', 'sab'],
    ['rOtSupportActionOtUnique', 'saou'],
    ['rOtTensionData', 'otd'],
    ['rOtTrainParam', 'otp'],
    ['rOtWeaponData', 'owp'],
    ['rPlBaseCmd', 'plbasecmd'],
    ['rPlCmdTblList', 'plcmdtbllist'],
    ['rPlayerGimmickType', 'plgmktype'],
    ['rPlayerManyAttacks', 'pma'],
    ['rPlayerPartsDisp', 'plpartsdisp'],
    ['rPlayerWeaponList', 'plweplist'],
    ['rPointPos', 'pntpos'],
    ['rProofEffectColorControl', 'pec'],
    ['rProofEffectList', 'pel'],
    ['rProofEffectMotSequenceList', 'psl'],
    ['rProofEffectParamScript', 'pep'],
    ['rQuestGroup', 'qsg'],
    ['rRapidshotData', 'raps'],
    ['rRelationData', 'rlt'],
    ['rRem', 'rem'],
    ['rSeFsAse', 'sfsa'],
    ['rSetEmMain', 'sem'],
    ['rSetItemData', 'sid'],
    ['rShell', 'shell'],
    ['rShellEffectParam', 'sep'],
    ['rSkillData', 'skd'],
    ['rSkillTypeData', 'skt'],
    ['rSoundBank', 'sbkr'],
    ['rSoundEQ', 'equr'],
    ['rSoundRequest', 'srqr'],
    ['rSoundReverb', 'revr_ctr'],
    ['rSoundSourceADPCM', 'mca'],
    ['rSoundStreamRequest', 'stqr'],
    ['rSquatshotData', 'squs'],
    ['rSupplyList', 'sup'],
    ['rSupportGaugeValue', 'spval'],
    ['rTameshotData', 'tams'],
    ['rWeapon00BaseData', 'w00d'],
    ['rWeapon00LevelData', 'w00d'],
    ['rWeapon00MsgData', 'w00m'],
    ['rWeapon01BaseData', 'w01d'],
    ['rWeapon01LevelData', 'w01d'],
    ['rWeapon01MsgData', 'w01m'],
    ['rWeapon02BaseData', 'w02d'],
    ['rWeapon02LevelData', 'w02d'],
    ['rWeapon02MsgData', 'w02m'],
    ['rWeapon03BaseData', 'w03d'],
    ['rWeapon03LevelData', 'w03d'],
    ['rWeapon03MsgData', 'w03m'],
    ['rWeapon04BaseData', 'w04d'],
    ['rWeapon04LevelData', 'w04d'],
    ['rWeapon04MsgData', 'w04m'],
    ['rWeapon06BaseData', 'w06d'],
    ['rWeapon06LevelData', 'w06d'],
    ['rWeapon06MsgData', 'w06m'],
    ['rWeapon07BaseData', 'w07d'],
    ['rWeapon07LevelData', 'w07d'],
    ['rWeapon07MsgData', 'w07m'],
    ['rWeapon08BaseData', 'w08d'],
    ['rWeapon08LevelData', 'w08d'],
    ['rWeapon08MsgData', 'w08m'],
    ['rWeapon09BaseData', 'w09d'],
    ['rWeapon09LevelData', 'w09d'],
    ['rWeapon09MsgData', 'w09m'],
    ['rWeapon10BaseData', 'w10d'],
    ['rWeapon10LevelData', 'w10d'],
    ['rWeapon10MsgData', 'w10m'],
    ['rWeapon11BaseData', 'w11d'],
    ['rWeapon11LevelData', 'w11d'],
    ['rWeapon11MsgData', 'w11m'],
    ['rWeapon12BaseData', 'w12d'],
    ['rWeapon12LevelData', 'w12d'],
    ['rWeapon12MsgData', 'w12m'],
    ['rWeapon13BaseData', 'w13d'],
    ['rWeapon13LevelData', 'w13d'],
    ['rWeapon13MsgData', 'w13m'],
    ['rWeapon14BaseData', 'w14d'],
    ['rWeapon14LevelData', 'w14d'],
    ['rWeapon14MsgData', 'w14m'],
    # Monster Hunter X file types
    ['rAcNyanterEquip', 'ane'],
    ['rAcPlayerEquip', 'ape'],
    ['rAreaConnect', 'acn'],
    ['rArmorCreateData', 'arcd'],
    ['rArmorProcessData', 'apd'],
    ['rBui', 'bui'],
    ['rCatSkillData', 'cskd'],
    ['rDLCOtomoInfo', 'doi'],
    ['rDecoCreateData', 'dcd'],
    ['rEquipShopListA00', 'sla00'],
    ['rEquipShopListW00', 'slw00'],
    ['rEquipShopListW01', 'slw01'],
    ['rEquipShopListW02', 'slw02'],
    ['rEquipShopListW03', 'slw03'],
    ['rEquipShopListW04', 'slw04'],
    ['rEquipShopListW06', 'slw06'],
    ['rEquipShopListW07', 'slw07'],
    ['rEquipShopListW08', 'slw08'],
    ['rEquipShopListW09', 'slw09'],
    ['rEquipShopListW10', 'slw10'],
    ['rEquipShopListW11', 'slw11'],
    ['rEquipShopListW12', 'slw12'],
    ['rEquipShopListW13', 'slw13'],
    ['rEquipShopListW14', 'slw14'],
    ['rFloorLvData', 'fld'],
    ['rFreeHuntData', 'fht'],
    ['rGeyserPointData', 'gpd'],
    ['rGuestEffectiveAttr', 'atr'],
    ['rGuestQuestData', 'mib'],
    ['rGuestRemData', 'rem'],
    ['rInsectAttrFeed', 'iaf'],
    ['rInsectGrowFeed', 'igf'],
    ['rItemCategoryTypeData', 'ict'],
    ['rKitchenListGrillItem', 'kcg'],
    ['rKitchenListMenu', 'kcm'],
    ['rKitchenListSkillAlcohol', 'kca'],
    ['rKitchenListSkillRandom', 'kcr'],
    ['rKitchenListSkillSet', 'kcs'],
    ['rKitchenListSuccessTable1', 'kc1'],
    ['rKitchenListSuccessTable2', 'kc2'],
    ['rKitchenListSuccessTable3', 'kc3'],
    ['rMonNyanAdventItem', 'mai'],
    ['rMonNyanCirclePattern', 'mcn'],
    ['rMonNyanCommonMaterial', 'mcm'],
    ['rMonNyanExp', 'mex'],
    ['rMonNyanLotAdvent', 'mla'],
    ['rMonNyanLotCommon', 'mlc'],
    ['rMonNyanLotEnemy', 'mle'],
    ['rMonNyanReward', 'mri'],
    ['rMonNyanRewardEnemy', 'mre'],
    ['rMonNyanRewardSecret', 'mrs'],
    ['rMonNyanVillagePoint', 'mvp'],
    ['rNpcBaseData', 'npcBd'],
    ['rNpcBaseData_ID', 'npcId'],
    ['rNpcBaseData_Mdl', 'npcMdl'],
    ['rNpcInitScript', 'nis'],
    ['rNpcLocateData', 'nld'],
    ['rNpcMoveData', 'npcMd'],
    ['rNpcSubData', 'npcSd'],
    ['rNpcTalkData', 'ntd'],
    ['rOtEquipCreate', 'oec'],
    ['rOtIniLot', 'otil'],
    ['rOtLotOwnSkill', 'olsk'],
    ['rOtLotOwnSupport', 'olos'],
    ['rOtParamLot', 'opl'],
    ['rOtPointTable', 'otpt'],
    ['rPieceCreateList', 'pcl'],
    ['rSansaijijiExchange', 'ssjje'],
    ['rSansaijijiPresent', 'ssjjp'],
    ['rShopList', 'slt'],
    ['rShopListSale', 'sls'],
    ['rSpActData', 'sad'],
    ['rTradeDeliveryList', 'trdl'],
    ['rTradeItemList', 'tril'],
    ['rTradeLimitedItemList', 'tlil'],
    ['rTradeLotList', 'trll'],
    ['rTradePointItemList', 'tpil'],
    ['rTutorialCylinderData', 'tucyl'],
    ['rTutorialFlowData', 'tuto'],
    ['rVillageFirstPos', 'vfp'],
    ['rWeaponCreateData', 'wcd'],
    ['rWeaponProcessData', 'wpd'],
    # Monster Hunter XX file types
    #['rAIDynamicLayout', ''],
    #['rAIPathBase', ''],
    #['rAIPathBaseXml', ''],
    #['rAIWayPointGraph', ''],
    #['rActParam', ''],
    #['rActionUseParam', ''],
    ['rAlchemyData', 'alc'],
    ['rAngleLimitData', 'AngleLimit'],
    #['rChain', ''],
    #['rCnsIK', ''],
    #['rCnsJointOffset', ''],
    #['rCnsMatrix', ''],
    #['rCnsTinyIK', ''],
    ['rCoinTradeList', 'ctl'],
    #['rCollisionHeightField', ''],
    #['rCollisionObj', ''],
    #['rConstraint', ''],
    #['rConvexHull', ''],
    #['rDLCItemPackInfo', ''],
    #['rDLCUpdateInfo', ''],
    #['rDebugActionData', ''],
    #['rDebugAtkActSet', ''],
    #['rDebugAtkActSet', ''],
    #['rEffect2D', ''],
    #['rEffectStrip', ''],
    #['rEmSetData', ''],
    #['rEnemyDataTable', ''],
    #['rEnemyDebugSetData', ''],
    #['rFestaResource', ''],
    #['rGeometry2', ''],
    #['rGeometry2', ''],
    #['rGeometry2Group', ''],
    #['rGeometry3', ''],
    #['rGrass', ''],
    #['rMovie', ''],
    #['rMovieOnMemory', ''],
    #['rNavigationMesh', ''],
    #['rNulls', ''],
    #['rOtodokeConditionList', ''],
    ['rOtodokeSetList', 'ots'],
    #['rPastQuestGroup', ''],
    #['rPlayerDummyAction', ''],
    ['rQuestDaily', 'qdm'],
    ['rQuestLink', 'qdl'],
    ['rQuestPlus', 'qdp'],
    #['rRenderTargetTexture', ''],
    ['rResearchReinforce', 'ots'],
    #['rResourceSample', ''],
    #['rSoundSource', ''],
    #['rSoundSourceWav', ''],
    #['rTrialArts', ''],
    #['rTrialBowBottle', ''],
    #['rTrialBowShot', ''],
    #['rTrialDataCommon', ''],
    #['rTrialDataNyanter', ''],
    #['rTrialEquipData', ''],
    #['rTrialEquipOtomo', ''],
    #['rTrialEquipParam', ''],
    #['rTrialHeavyBowgunData', ''],
    #['rTrialItemPoach', ''],
    #['rTrialLightBowgun', ''],
    #['rTrialLoadShellCount', ''],
    #['rTrialOtomoParam', ''],
    #['rVertices', ''],
    #['rVibration', ''],
    #['rVramLoadList', '']
]


def gen_file_type_codes():
    return [(zlib.crc32(file_type[0].encode()) ^ 0xffffffff) & 0x7fffffff for file_type in file_types]


def extract_arc(arc_file, output_path, file_list):
    """
    Extrae los archivos preservando el nombre de la TOC y añadiendo .<TYPECODE>.
    Limpia caracteres nulos y espacios de cada componente de la ruta para evitar
    ValueError: embedded null character o nombres inválidos en Windows.
    """
    if not os.path.isdir(output_path):
        raise ValueError('output path: must be existing directory')
    with open(arc_file, 'rb') as arc:
        magic, version, file_count, unknown = struct.unpack('4sHHI', arc.read(12))
        if magic != b'ARC\x00':
            raise ValueError('header: invalid magic')
        if version not in [0x13, 0x11]:  # 0x13 = MH4U, 0x11 = MHX
            raise ValueError('header: invalid version')
        file_type_codes = gen_file_type_codes()
        toc = arc.read(file_count * 0x50)
        file_list_f = None
        if file_list:
            file_list_f = open(file_list, 'w', encoding='utf-8')
        for i in range(file_count):
            file_name_bytes, file_type_code, compressed_size, size, offset = struct.unpack(
                '64sIIII', toc[i*0x50:(i+1)*0x50]
            )

            # Decodificar bytes a str (mantener bytes válidos). NO introducimos literales \x00.
            # Luego eliminamos cualquier carácter nulo real y recortamos espacios de cada componente.
            raw = file_name_bytes.decode('latin-1', errors='ignore')  # latin-1 preserva byte-to-char 1:1
            # Eliminar caracteres nulos reales
            raw = raw.replace('\x00', '')
            # Separar por backslash (TOC usa '\') y limpiar cada componente
            parts = [p.strip() for p in raw.split('\\') if p and p.strip() != '']
            if parts:
                # limpiar cada componente de caracteres problemáticos
                clean_parts = []
                for p in parts:
                    # quitar nulos que pudieran quedar y recortar espacios extremos
                    p = p.replace('\x00', '').strip()
                    # opcional: eliminar caracteres de control remanentes
                    p = ''.join(ch for ch in p if ord(ch) >= 32)
                    if p:
                        clean_parts.append(p)
                if clean_parts:
                    base_rel = os.path.normpath(os.path.join(*clean_parts))
                else:
                    base_rel = f'file_{i:04d}'
            else:
                base_rel = f'file_{i:04d}'

            # Generar extensión hex del type code (8 dígitos uppercase)
            hex_ext = '{:08X}'.format(file_type_code)

            # Añadir siempre la extensión tipo .1BBFD18E (sin duplicados)
            if base_rel.lower().endswith('.' + hex_ext.lower()):
                rel_path = base_rel
            else:
                rel_path = base_rel + '.' + hex_ext

            # Asegurar que rel_path no contenga bytes nulos ni caracteres de control
            rel_path = rel_path.replace('\x00', '')
            rel_path = ''.join(ch for ch in rel_path if ord(ch) >= 32)

            # Registrar en filelist (si se pidió)
            if file_list_f:
                file_list_f.write(rel_path + '\n')

            # leer y descomprimir los datos
            if version == 0x13:
                size &= 0x0fffffff
            else:
                size &= 0x1fffffff

            print('extracting: {}, type code: {:08X}, compressed size: {}, size: {}'.format(
                rel_path, file_type_code, compressed_size, size
            ))

            arc.seek(offset)
            comp_data = arc.read(compressed_size)
            if len(comp_data) != compressed_size:
                raise ValueError('table of contents: wrong compressed file size')
            file_data = zlib.decompress(comp_data)
            if len(file_data) != size:
                raise ValueError('table of contents: wrong file size')

            out_path = os.path.join(output_path, rel_path)
            out_dir = os.path.dirname(out_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            else:
                os.makedirs(output_path, exist_ok=True)

            # Finalmente escribir el archivo (ruta ya sanitizada)
            with open(out_path, 'wb') as out_f:
                out_f.write(file_data)

        if file_list_f:
            file_list_f.close()


def create_arc(arc_file, input_files):
    arc = open(arc_file, 'wb')
    arc.write(struct.pack('4sHHI', b'ARC\x00', 0x11, len(input_files), 0))
    file_type_codes = gen_file_type_codes()
    file_data_pos = len(input_files) * 0x50 + 12

    for i in range(len(input_files)):
        file_path = input_files[i]
        file_name, file_extension = os.path.splitext(file_path)
        file_name = file_name.replace('/', '\\')
        file_extension = file_extension.lstrip('.').upper()

        # Determinar type code
        type_code = 0
        if file_extension in [ft[1].upper() for ft in file_types]:
            # Buscar en la tabla file_types
            for j, ft in enumerate(file_types):
                if file_extension == ft[1].upper():
                    type_code = file_type_codes[j]
                    break
        elif len(file_extension) == 8:
            try:
                type_code = int(file_extension, 16)
            except ValueError:
                type_code = 0  # fallback si no es hex
        else:
            type_code = 0  # fallback

        # Leer archivo y comprimir
        file_data = open(file_path, 'rb').read()
        size = len(file_data) | 0x40000000
        file_data = zlib.compress(file_data)
        compressed_size = len(file_data)

        # Escribir entrada TOC
        arc.seek(i * 0x50 + 12)
        arc.write(struct.pack('64sIIII', file_name.encode(), type_code, compressed_size, size, file_data_pos))

        # Escribir datos comprimidos
        arc.seek(file_data_pos)
        arc.write(file_data)
        file_data_pos += len(file_data)

    arc.close()

parser = argparse.ArgumentParser(description='Extracts files from an ARC file from MH4U and MHX')
subparsers = parser.add_subparsers(dest='mode')
parser_x = subparsers.add_parser('x')
parser_x.add_argument('--filelist', help='file list output')
parser_x.add_argument('inputfile', help='ARC input file')
parser_x.add_argument('outputpath', nargs='?', default='./', help='output path')
parser_c = subparsers.add_parser('c')
parser_c.add_argument('--filelist', help='file list input')
parser_c.add_argument('outputfile', help='ARC output file')
parser_c.add_argument('inputfile', nargs='*', help='input files')
args = parser.parse_args()

if args.mode == 'x':
    extract_arc(args.inputfile, args.outputpath, args.filelist)
elif args.mode == 'c':
    input_files = []
    try:
        for line in open(args.filelist, 'r'):
            line = line.strip()
            if line != '':
                input_files.append(line)
    except:
        pass
    for input_file in args.inputfile:
        if os.path.isdir(input_file):
            for dirpath, dirnames, filenames in os.walk(input_file):
                for file_name in filenames:
                    input_files.append(os.path.join(dirpath, file_name))
        else:
            input_files.append(input_file)
    create_arc(args.outputfile, input_files)
