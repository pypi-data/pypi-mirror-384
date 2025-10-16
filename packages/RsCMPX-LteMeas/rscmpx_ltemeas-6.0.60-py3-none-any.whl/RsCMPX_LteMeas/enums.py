from enum import Enum


# noinspection SpellCheckingInspection
class Band(Enum):
	"""64 Members, OB1 ... OB9"""
	OB1 = 0
	OB10 = 1
	OB106 = 2
	OB11 = 3
	OB12 = 4
	OB13 = 5
	OB14 = 6
	OB15 = 7
	OB16 = 8
	OB17 = 9
	OB18 = 10
	OB19 = 11
	OB2 = 12
	OB20 = 13
	OB21 = 14
	OB22 = 15
	OB23 = 16
	OB24 = 17
	OB25 = 18
	OB250 = 19
	OB26 = 20
	OB27 = 21
	OB28 = 22
	OB3 = 23
	OB30 = 24
	OB31 = 25
	OB33 = 26
	OB34 = 27
	OB35 = 28
	OB36 = 29
	OB37 = 30
	OB38 = 31
	OB39 = 32
	OB4 = 33
	OB40 = 34
	OB41 = 35
	OB42 = 36
	OB43 = 37
	OB44 = 38
	OB45 = 39
	OB46 = 40
	OB47 = 41
	OB48 = 42
	OB49 = 43
	OB5 = 44
	OB50 = 45
	OB51 = 46
	OB52 = 47
	OB53 = 48
	OB6 = 49
	OB65 = 50
	OB66 = 51
	OB68 = 52
	OB7 = 53
	OB70 = 54
	OB71 = 55
	OB72 = 56
	OB73 = 57
	OB74 = 58
	OB8 = 59
	OB85 = 60
	OB87 = 61
	OB88 = 62
	OB9 = 63


# noinspection SpellCheckingInspection
class BandwidthNarrow(Enum):
	"""4 Members, M010 ... M080"""
	M010 = 0
	M020 = 1
	M040 = 2
	M080 = 3


# noinspection SpellCheckingInspection
class CarrAggrLocalOscLocation(Enum):
	"""3 Members, AUTO ... CECC"""
	AUTO = 0
	CACB = 1
	CECC = 2


# noinspection SpellCheckingInspection
class CarrAggrMaping(Enum):
	"""9 Members, INV ... SCC7"""
	INV = 0
	PCC = 1
	SCC1 = 2
	SCC2 = 3
	SCC3 = 4
	SCC4 = 5
	SCC5 = 6
	SCC6 = 7
	SCC7 = 8


# noinspection SpellCheckingInspection
class CarrAggrMode(Enum):
	"""4 Members, ICD ... OFF"""
	ICD = 0
	ICE = 1
	INTRaband = 2
	OFF = 3


# noinspection SpellCheckingInspection
class ChannelBandwidth(Enum):
	"""6 Members, B014 ... B200"""
	B014 = 0
	B030 = 1
	B050 = 2
	B100 = 3
	B150 = 4
	B200 = 5


# noinspection SpellCheckingInspection
class ChannelTypeDetection(Enum):
	"""3 Members, AUTO ... PUSCh"""
	AUTO = 0
	PUCCh = 1
	PUSCh = 2


# noinspection SpellCheckingInspection
class ChannelTypeVewFilter(Enum):
	"""4 Members, OFF ... PUSCh"""
	OFF = 0
	ON = 1
	PUCCh = 2
	PUSCh = 3


# noinspection SpellCheckingInspection
class CmwsConnector(Enum):
	"""48 Members, R11 ... RB8"""
	R11 = 0
	R12 = 1
	R13 = 2
	R14 = 3
	R15 = 4
	R16 = 5
	R17 = 6
	R18 = 7
	R21 = 8
	R22 = 9
	R23 = 10
	R24 = 11
	R25 = 12
	R26 = 13
	R27 = 14
	R28 = 15
	R31 = 16
	R32 = 17
	R33 = 18
	R34 = 19
	R35 = 20
	R36 = 21
	R37 = 22
	R38 = 23
	R41 = 24
	R42 = 25
	R43 = 26
	R44 = 27
	R45 = 28
	R46 = 29
	R47 = 30
	R48 = 31
	RA1 = 32
	RA2 = 33
	RA3 = 34
	RA4 = 35
	RA5 = 36
	RA6 = 37
	RA7 = 38
	RA8 = 39
	RB1 = 40
	RB2 = 41
	RB3 = 42
	RB4 = 43
	RB5 = 44
	RB6 = 45
	RB7 = 46
	RB8 = 47


# noinspection SpellCheckingInspection
class CyclicPrefix(Enum):
	"""2 Members, EXTended ... NORMal"""
	EXTended = 0
	NORMal = 1


# noinspection SpellCheckingInspection
class FrameStructure(Enum):
	"""2 Members, T1 ... T2"""
	T1 = 0
	T2 = 1


# noinspection SpellCheckingInspection
class LaggingExclPeriod(Enum):
	"""3 Members, MS05 ... OFF"""
	MS05 = 0
	MS25 = 1
	OFF = 2


# noinspection SpellCheckingInspection
class LeadingExclPeriod(Enum):
	"""2 Members, MS25 ... OFF"""
	MS25 = 0
	OFF = 1


# noinspection SpellCheckingInspection
class ListMode(Enum):
	"""2 Members, ONCE ... SEGMent"""
	ONCE = 0
	SEGMent = 1


# noinspection SpellCheckingInspection
class LocalOscLocation(Enum):
	"""2 Members, CCB ... CN"""
	CCB = 0
	CN = 1


# noinspection SpellCheckingInspection
class LowHigh(Enum):
	"""2 Members, HIGH ... LOW"""
	HIGH = 0
	LOW = 1


# noinspection SpellCheckingInspection
class MeasCarrier(Enum):
	"""2 Members, PCC ... SCC1"""
	PCC = 0
	SCC1 = 1


# noinspection SpellCheckingInspection
class MeasCarrierB(Enum):
	"""8 Members, PCC ... SCC7"""
	PCC = 0
	SCC1 = 1
	SCC2 = 2
	SCC3 = 3
	SCC4 = 4
	SCC5 = 5
	SCC6 = 6
	SCC7 = 7


# noinspection SpellCheckingInspection
class MeasCarrierEnhanced(Enum):
	"""4 Members, CC1 ... CC4"""
	CC1 = 0
	CC2 = 1
	CC3 = 2
	CC4 = 3


# noinspection SpellCheckingInspection
class MeasFilter(Enum):
	"""2 Members, BANDpass ... GAUSs"""
	BANDpass = 0
	GAUSs = 1


# noinspection SpellCheckingInspection
class MeasurementMode(Enum):
	"""3 Members, MELMode ... TMODe"""
	MELMode = 0
	NORMal = 1
	TMODe = 2


# noinspection SpellCheckingInspection
class MeasureSlot(Enum):
	"""3 Members, ALL ... MS1"""
	ALL = 0
	MS0 = 1
	MS1 = 2


# noinspection SpellCheckingInspection
class MevAcquisitionMode(Enum):
	"""2 Members, SLOT ... SUBFrame"""
	SLOT = 0
	SUBFrame = 1


# noinspection SpellCheckingInspection
class Mode(Enum):
	"""2 Members, FDD ... TDD"""
	FDD = 0
	TDD = 1


# noinspection SpellCheckingInspection
class ModScheme(Enum):
	"""5 Members, AUTO ... QPSK"""
	AUTO = 0
	Q16 = 1
	Q256 = 2
	Q64 = 3
	QPSK = 4


# noinspection SpellCheckingInspection
class Modulation(Enum):
	"""4 Members, Q16 ... QPSK"""
	Q16 = 0
	Q256 = 1
	Q64 = 2
	QPSK = 3


# noinspection SpellCheckingInspection
class NetworkSharing(Enum):
	"""3 Members, FSHared ... OCONnection"""
	FSHared = 0
	NSHared = 1
	OCONnection = 2


# noinspection SpellCheckingInspection
class NetworkSigValue(Enum):
	"""32 Members, NS01 ... NS32"""
	NS01 = 0
	NS02 = 1
	NS03 = 2
	NS04 = 3
	NS05 = 4
	NS06 = 5
	NS07 = 6
	NS08 = 7
	NS09 = 8
	NS10 = 9
	NS11 = 10
	NS12 = 11
	NS13 = 12
	NS14 = 13
	NS15 = 14
	NS16 = 15
	NS17 = 16
	NS18 = 17
	NS19 = 18
	NS20 = 19
	NS21 = 20
	NS22 = 21
	NS23 = 22
	NS24 = 23
	NS25 = 24
	NS26 = 25
	NS27 = 26
	NS28 = 27
	NS29 = 28
	NS30 = 29
	NS31 = 30
	NS32 = 31


# noinspection SpellCheckingInspection
class NetworkSigValueNoCarrAggr(Enum):
	"""288 Members, NS01 ... NS99"""
	NS01 = 0
	NS02 = 1
	NS03 = 2
	NS04 = 3
	NS05 = 4
	NS06 = 5
	NS07 = 6
	NS08 = 7
	NS09 = 8
	NS10 = 9
	NS100 = 10
	NS101 = 11
	NS102 = 12
	NS103 = 13
	NS104 = 14
	NS105 = 15
	NS106 = 16
	NS107 = 17
	NS108 = 18
	NS109 = 19
	NS11 = 20
	NS110 = 21
	NS111 = 22
	NS112 = 23
	NS113 = 24
	NS114 = 25
	NS115 = 26
	NS116 = 27
	NS117 = 28
	NS118 = 29
	NS119 = 30
	NS12 = 31
	NS120 = 32
	NS121 = 33
	NS122 = 34
	NS123 = 35
	NS124 = 36
	NS125 = 37
	NS126 = 38
	NS127 = 39
	NS128 = 40
	NS129 = 41
	NS13 = 42
	NS130 = 43
	NS131 = 44
	NS132 = 45
	NS133 = 46
	NS134 = 47
	NS135 = 48
	NS136 = 49
	NS137 = 50
	NS138 = 51
	NS139 = 52
	NS14 = 53
	NS140 = 54
	NS141 = 55
	NS142 = 56
	NS143 = 57
	NS144 = 58
	NS145 = 59
	NS146 = 60
	NS147 = 61
	NS148 = 62
	NS149 = 63
	NS15 = 64
	NS150 = 65
	NS151 = 66
	NS152 = 67
	NS153 = 68
	NS154 = 69
	NS155 = 70
	NS156 = 71
	NS157 = 72
	NS158 = 73
	NS159 = 74
	NS16 = 75
	NS160 = 76
	NS161 = 77
	NS162 = 78
	NS163 = 79
	NS164 = 80
	NS165 = 81
	NS166 = 82
	NS167 = 83
	NS168 = 84
	NS169 = 85
	NS17 = 86
	NS170 = 87
	NS171 = 88
	NS172 = 89
	NS173 = 90
	NS174 = 91
	NS175 = 92
	NS176 = 93
	NS177 = 94
	NS178 = 95
	NS179 = 96
	NS18 = 97
	NS180 = 98
	NS181 = 99
	NS182 = 100
	NS183 = 101
	NS184 = 102
	NS185 = 103
	NS186 = 104
	NS187 = 105
	NS188 = 106
	NS189 = 107
	NS19 = 108
	NS190 = 109
	NS191 = 110
	NS192 = 111
	NS193 = 112
	NS194 = 113
	NS195 = 114
	NS196 = 115
	NS197 = 116
	NS198 = 117
	NS199 = 118
	NS20 = 119
	NS200 = 120
	NS201 = 121
	NS202 = 122
	NS203 = 123
	NS204 = 124
	NS205 = 125
	NS206 = 126
	NS207 = 127
	NS208 = 128
	NS209 = 129
	NS21 = 130
	NS210 = 131
	NS211 = 132
	NS212 = 133
	NS213 = 134
	NS214 = 135
	NS215 = 136
	NS216 = 137
	NS217 = 138
	NS218 = 139
	NS219 = 140
	NS22 = 141
	NS220 = 142
	NS221 = 143
	NS222 = 144
	NS223 = 145
	NS224 = 146
	NS225 = 147
	NS226 = 148
	NS227 = 149
	NS228 = 150
	NS229 = 151
	NS23 = 152
	NS230 = 153
	NS231 = 154
	NS232 = 155
	NS233 = 156
	NS234 = 157
	NS235 = 158
	NS236 = 159
	NS237 = 160
	NS238 = 161
	NS239 = 162
	NS24 = 163
	NS240 = 164
	NS241 = 165
	NS242 = 166
	NS243 = 167
	NS244 = 168
	NS245 = 169
	NS246 = 170
	NS247 = 171
	NS248 = 172
	NS249 = 173
	NS25 = 174
	NS250 = 175
	NS251 = 176
	NS252 = 177
	NS253 = 178
	NS254 = 179
	NS255 = 180
	NS256 = 181
	NS257 = 182
	NS258 = 183
	NS259 = 184
	NS26 = 185
	NS260 = 186
	NS261 = 187
	NS262 = 188
	NS263 = 189
	NS264 = 190
	NS265 = 191
	NS266 = 192
	NS267 = 193
	NS268 = 194
	NS269 = 195
	NS27 = 196
	NS270 = 197
	NS271 = 198
	NS272 = 199
	NS273 = 200
	NS274 = 201
	NS275 = 202
	NS276 = 203
	NS277 = 204
	NS278 = 205
	NS279 = 206
	NS28 = 207
	NS280 = 208
	NS281 = 209
	NS282 = 210
	NS283 = 211
	NS284 = 212
	NS285 = 213
	NS286 = 214
	NS287 = 215
	NS288 = 216
	NS29 = 217
	NS30 = 218
	NS31 = 219
	NS32 = 220
	NS33 = 221
	NS34 = 222
	NS35 = 223
	NS36 = 224
	NS37 = 225
	NS38 = 226
	NS39 = 227
	NS40 = 228
	NS41 = 229
	NS42 = 230
	NS43 = 231
	NS44 = 232
	NS45 = 233
	NS46 = 234
	NS47 = 235
	NS48 = 236
	NS49 = 237
	NS50 = 238
	NS51 = 239
	NS52 = 240
	NS53 = 241
	NS54 = 242
	NS55 = 243
	NS56 = 244
	NS57 = 245
	NS58 = 246
	NS59 = 247
	NS60 = 248
	NS61 = 249
	NS62 = 250
	NS63 = 251
	NS64 = 252
	NS65 = 253
	NS66 = 254
	NS67 = 255
	NS68 = 256
	NS69 = 257
	NS70 = 258
	NS71 = 259
	NS72 = 260
	NS73 = 261
	NS74 = 262
	NS75 = 263
	NS76 = 264
	NS77 = 265
	NS78 = 266
	NS79 = 267
	NS80 = 268
	NS81 = 269
	NS82 = 270
	NS83 = 271
	NS84 = 272
	NS85 = 273
	NS86 = 274
	NS87 = 275
	NS88 = 276
	NS89 = 277
	NS90 = 278
	NS91 = 279
	NS92 = 280
	NS93 = 281
	NS94 = 282
	NS95 = 283
	NS96 = 284
	NS97 = 285
	NS98 = 286
	NS99 = 287


# noinspection SpellCheckingInspection
class ParameterSetMode(Enum):
	"""2 Members, GLOBal ... LIST"""
	GLOBal = 0
	LIST = 1


# noinspection SpellCheckingInspection
class Path(Enum):
	"""2 Members, NETWork ... STANdalone"""
	NETWork = 0
	STANdalone = 1


# noinspection SpellCheckingInspection
class PeriodPreamble(Enum):
	"""3 Members, MS05 ... MS20"""
	MS05 = 0
	MS10 = 1
	MS20 = 2


# noinspection SpellCheckingInspection
class PucchFormat(Enum):
	"""7 Members, F1 ... F3"""
	F1 = 0
	F1A = 1
	F1B = 2
	F2 = 3
	F2A = 4
	F2B = 5
	F3 = 6


# noinspection SpellCheckingInspection
class RbTableChannelType(Enum):
	"""8 Members, DL ... SSUB"""
	DL = 0
	NONE = 1
	PSBCh = 2
	PSCCh = 3
	PSSCh = 4
	PUCCh = 5
	PUSCh = 6
	SSUB = 7


# noinspection SpellCheckingInspection
class Rbw(Enum):
	"""3 Members, K030 ... M1"""
	K030 = 0
	K100 = 1
	M1 = 2


# noinspection SpellCheckingInspection
class RbwExtended(Enum):
	"""6 Members, K030 ... M1"""
	K030 = 0
	K050 = 1
	K100 = 2
	K150 = 3
	K200 = 4
	M1 = 5


# noinspection SpellCheckingInspection
class Repeat(Enum):
	"""2 Members, CONTinuous ... SINGleshot"""
	CONTinuous = 0
	SINGleshot = 1


# noinspection SpellCheckingInspection
class ResourceState(Enum):
	"""8 Members, ACTive ... RUN"""
	ACTive = 0
	ADJusted = 1
	INValid = 2
	OFF = 3
	PENDing = 4
	QUEued = 5
	RDY = 6
	RUN = 7


# noinspection SpellCheckingInspection
class ResultStatus2(Enum):
	"""10 Members, DC ... ULEU"""
	DC = 0
	INV = 1
	NAV = 2
	NCAP = 3
	OFF = 4
	OFL = 5
	OK = 6
	UFL = 7
	ULEL = 8
	ULEU = 9


# noinspection SpellCheckingInspection
class RetriggerFlag(Enum):
	"""4 Members, IFPNarrow ... ON"""
	IFPNarrow = 0
	IFPower = 1
	OFF = 2
	ON = 3


# noinspection SpellCheckingInspection
class SegmentChannelTypeExtended(Enum):
	"""6 Members, AUTO ... PUSCh"""
	AUTO = 0
	PSBCh = 1
	PSCCh = 2
	PSSCh = 3
	PUCCh = 4
	PUSCh = 5


# noinspection SpellCheckingInspection
class SidelinkChannelType(Enum):
	"""3 Members, PSBCh ... PSSCh"""
	PSBCh = 0
	PSCCh = 1
	PSSCh = 2


# noinspection SpellCheckingInspection
class SignalSlope(Enum):
	"""2 Members, FEDGe ... REDGe"""
	FEDGe = 0
	REDGe = 1


# noinspection SpellCheckingInspection
class SignalType(Enum):
	"""2 Members, SL ... UL"""
	SL = 0
	UL = 1


# noinspection SpellCheckingInspection
class StopCondition(Enum):
	"""2 Members, NONE ... SLFail"""
	NONE = 0
	SLFail = 1


# noinspection SpellCheckingInspection
class SyncMode(Enum):
	"""2 Members, ENHanced ... NORMal"""
	ENHanced = 0
	NORMal = 1


# noinspection SpellCheckingInspection
class TargetStateA(Enum):
	"""3 Members, OFF ... RUN"""
	OFF = 0
	RDY = 1
	RUN = 2


# noinspection SpellCheckingInspection
class TargetSyncState(Enum):
	"""2 Members, ADJusted ... PENDing"""
	ADJusted = 0
	PENDing = 1


# noinspection SpellCheckingInspection
class TimeMask(Enum):
	"""3 Members, GOO ... SBLanking"""
	GOO = 0
	PPSRs = 1
	SBLanking = 2


# noinspection SpellCheckingInspection
class TraceSelect(Enum):
	"""3 Members, AVERage ... MAXimum"""
	AVERage = 0
	CURRent = 1
	MAXimum = 2


# noinspection SpellCheckingInspection
class UplinkChannelType(Enum):
	"""2 Members, PUCCh ... PUSCh"""
	PUCCh = 0
	PUSCh = 1


# noinspection SpellCheckingInspection
class ViewMev(Enum):
	"""15 Members, ACLR ... TXM"""
	ACLR = 0
	BLER = 1
	ESFLatness = 2
	EVMagnitude = 3
	EVMC = 4
	IEMissions = 5
	IQ = 6
	MERRor = 7
	OVERview = 8
	PDYNamics = 9
	PERRor = 10
	PMONitor = 11
	RBATable = 12
	SEMask = 13
	TXM = 14


# noinspection SpellCheckingInspection
class ViewPrach(Enum):
	"""10 Members, EVMagnitude ... TXM"""
	EVMagnitude = 0
	EVPReamble = 1
	EVSYmbol = 2
	IQ = 3
	MERRor = 4
	OVERview = 5
	PDYNamics = 6
	PERRor = 7
	PVPReamble = 8
	TXM = 9


# noinspection SpellCheckingInspection
class ViewSrs(Enum):
	"""1 Members, PDYNamics ... PDYNamics"""
	PDYNamics = 0
