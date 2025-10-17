lic_ = """
   Copyright 2025 Richard Tjörnhammar

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import pandas as pd
import numpy as np

__desc__ = """ Attenuation by atmospheric gases and related effects """

# Recommendation ITU-R P.676-13

TABLE1 = """50.474214
0.975
9.651
6.690
0.0
2.566
6.850
50.987745
2.529
8.653
7.170
0.0
2.246
6.800
51.503360
6.193
7.709
7.640
0.0
1.947
6.729
52.021429
14.320
6.819
8.110
0.0
1.667
6.640
52.542418
31.240
5.983
8.580
0.0
1.388
6.526
53.066934
64.290
5.201
9.060
0.0
1.349
6.206
53.595775
124.600
4.474
9.550
0.0
2.227
5.085
54.130025
227.300
3.800
9.960
0.0
3.170
3.750
54.671180
389.700
3.182
10.370
0.0
3.558
2.654
55.221384
627.100
2.618
10.890
0.0
2.560
2.952
55.783815
945.300
2.109
11.340
0.0
–1.172
6.135
56.264774
543.400
0.014
17.030
0.0
3.525
–0.978
56.363399
1331.800
1.654
11.890
0.0
–2.378
6.547
56.968211
1746.600
1.255
12.230
0.0
–3.545
6.451
57.612486
2120.100
0.910
12.620
0.0
–5.416
6.056
58.323877
2363.700
0.621
12.950
0.0
–1.932
0.436
58.446588
1442.100
0.083
14.910
0.0
6.768
–1.273
59.164204
2379.900
0.387
13.530
0.0
–6.561
2.309
59.590983
2090.700
0.207
14.080
0.0
6.957
–0.776
60.306056
2103.400
0.207
14.150
0.0
–6.395
0.699
60.434778
2438.000
0.386
13.390
0.0
6.342
–2.825
61.150562
2479.500
0.621
12.920
0.0
1.014
–0.584
61.800158
2275.900
0.910
12.630
0.0
5.014
–6.619
62.411220
1915.400
1.255
12.170
0.0
3.029
–6.759
62.486253
1503.000
0.083
15.130
0.0
–4.499
0.844
62.997984
1490.200
1.654
11.740
0.0
1.856
–6.675
63.568526
1078.000
2.108
11.340
0.0
0.658
–6.139
64.127775
728.700
2.617
10.880
0.0
–3.036
–2.895
64.678910
461.300
3.181
10.380
0.0
–3.968
–2.590
65.224078
274.000
3.800
9.960
0.0
–3.528
–3.680
65.764779
153.000
4.473
9.550
0.0
–2.548
–5.002
66.302096
80.400
5.200
9.060
0.0
–1.660
–6.091
66.836834
39.800
5.982
8.580
0.0
–1.680
–6.393
67.369601
18.560
6.818
8.110
0.0
–1.956
–6.475
67.900868
8.172
7.708
7.640
0.0
–2.216
–6.545
68.431006
3.397
8.652
7.170
0.0
–2.492
–6.600
68.960312
1.334
9.650
6.690
0.0
–2.773
-6.650
118.750334
940.300
0.010
16.640
0.0
-0.439
0.079
368.498246
67.400
0.048
16.400
0.0
0.000
0.000
424.763020
637.700
0.044
16.400
0.0
0.000
0.000
487.249273
237.400
0.049
16.000
0.0
0.000
0.000
715.392902
98.100
0.145
16.000
0.0
0.000
0.000
773.839490
572.300
0.141
16.200
0.0
0.000
0.000
834.145546
183.100
0.145
14.700
0.0
0.000
0.000""".replace("–","-")

TABLE2="""22.235080
.1079
2.144
26.38
.76
5.087
1.00
67.803960
.0011
8.732
28.58
.69
4.930
.82
119.995940
.0007
8.353
29.48
.70
4.780
.79
183.310087
2.273
.668
29.06
.77
5.022
.85
321.225630
.0470
6.179
24.04
.67
4.398
.54
325.152888
1.514
1.541
28.23
.64
4.893
.74
336.227764
.0010
9.825
26.93
.69
4.740
.61
380.197353
11.67
1.048
28.11
.54
5.063
.89
390.134508
.0045
7.347
21.52
.63
4.810
.55
437.346667
.0632
5.048
18.45
.60
4.230
.48
439.150807
.9098
3.595
20.07
.63
4.483
.52
443.018343
.1920
5.048
15.55
.60
5.083
.50
448.001085
10.41
1.405
25.64
.66
5.028
.67
470.888999
.3254
3.597
21.34
.66
4.506
.65
474.689092
1.260
2.379
23.20
.65
4.804
.64
488.490108
.2529
2.852
25.86
.69
5.201
.72
503.568532
.0372
6.731
16.12
.61
3.980
.43
504.482692
.0124
6.731
16.12
.61
4.010
.45
547.676440
.9785
.158
26.00
.70
4.500
1.00
552.020960
.1840
.158
26.00
.70
4.500
1.00
556.935985
497.0
.159
30.86
.69
4.552
1.00
620.700807
5.015
2.391
24.38
.71
4.856
.68
645.766085
.0067
8.633
18.00
.60
4.000
.50
658.005280
.2732
7.816
32.10
.69
4.140
1.00
752.033113
243.4
.396
30.86
.68
4.352
.84
841.051732
.0134
8.177
15.90
.33
5.760
.45
859.965698
.1325
8.055
30.60
.68
4.090
.84
899.303175
.0547
7.914
29.85
.68
4.530
.90
902.611085
.0386
8.429
28.65
.70
5.100
.95
906.205957
.1836
5.110
24.08
.70
4.700
.53
916.171582
8.400
1.441
26.73
.70
5.150
.78
923.112692
.0079
10.293
29.00
.70
5.000
.80
970.315022
9.009
1.919
25.50
.64
4.940
.67
987.926764
134.6
.257
29.85
.68
4.550
.90
1780.0
17506.
.952
196.3
2.00
24.15
5.00""".replace("–","-")

table1_df = pd.DataFrame(np.array([float(f) if len(f)>0 else 0 for f in TABLE1.split('\n')]).reshape(-1,7), columns=["f0","a1","a2","a3","a4","a5","a6"] )
table2_df = pd.DataFrame(np.array([float(f) if len(f)>0 else 0 for f in TABLE2.split('\n')]).reshape(-1,7), columns=["f0","b1","b2","b3","b4","b5","b6"] )

def environments_ITU_R_P_835( H=None , Z=None ):
    HtoZ = lambda h : 6356.766*h/(6356.766-h)
    ZtoH = lambda z : 6356.766*z/(6356.766+z)

    if H is None and Z is None :
        print("MUST SPECIFY A ALTITUDE HEIGHT TYPE (GEOPOTENTIAL OR GEOMETRIC)")
        exit(1)

    if H is None :
        H = ZtoH(Z)
    if Z is None :
        Z = HtoZ(H)

    a = [95.571899,-4.011801,6.424731*10**(-2),-4.789606*10**(-4),1.340543*10**(-6)]

    if True : # geopotential height 𝐻
        if H<=11 :
            T = 288.15-6.5*H
            p = 1013.25*( 288.15/(288.15-6.5*H) )**(-34.1632/6.5)
        elif H>11 and H<=20 :
            T = 216.65
            p = 226.3226*np.exp(-34.1632*(H-11)/216.65)
        elif H>20 and H<=32 :
            T = 216.65 + H - 20
            p = 54.74980*( 216.65/(216.65+(H-20)) )**(34.1632)
        elif H>32 and H<=47 :
            T = 228.65 + 2.8 *( H - 32 )
            p = 8.680422*( 228.65/( 228.65 + 2.8*(H-32)) )**(34.1632/2.8)
        elif H>47 and H<=51 :
            T = 270.65
            p = 1.109106*np.exp(-34.1632*(H-47)/270.65)
        elif H>51 and H<=71 :
            T = 270.65 - 2.8*( H - 51 )
            p = 0.6694167 * ( 270.65/(270.65-2.8*(H-51)) )**(-34.1632/2.8)
        elif H>71 and H<=84.852 :
            T = 214.65 - 2.0*( H - 71 )
            p = 0.03956649 * ( 214.65/(214.65-2.0*(H-71)) )**(-34.1632/2.0)
        else :
            if True : # geometric height
                p = np.sum([ ai*Z**i for (ai,i) in zip(a,range(len(a))) ])
                if Z>=86 and Z<91:
                    T = 186.8673 
                elif Z>=91 and Z<100:
                    T = 263.1905 - 76.3232*( 1 - ((Z-91)/19.9429)**2 )**0.5
                else :
                    print("ERROR")
    theta = 300/T

    water_vapor_density = 7.5 * np.exp(-Z*0.5)
    e = water_vapor_density * T / 216.7

    environment = [p,e,T,theta]
    return ( environment )

def linestrength_S(	type = "oxygen",
			p = 1 , e = 1, T = 300,
                        data = {"oxygen":table1_df , "water":table2_df} ) :
    """
p : dry air pressure (hPa)
e : water vapour partial pressure (hPa) (total barometric pressure, ptot = p + e)
T : temperature (K).
theta = 300/T
    """
    theta = 300/T
    S     = []
    df = data[type]
    if "oxygen" in type :
        f0 = df.loc[:,"f0"]
        a1 = df.loc[:,"a1"]
        a2 = df.loc[:,"a2"]
        S  = a1*10**(-7)*p*theta**3*np.exp(a2*(1-theta))
    if "water" in type :
        f0 = df.loc[:,"f0"]
        b1 = df.loc[:,"b1"]
        b2 = df.loc[:,"b2"]
        S  = b1*10**(-1)*e*theta**3.5*np.exp(b2*(1-theta))
    return S

def lineshape_F( freq,	type = "oxygen" ,
			p = 1 , e = 1, T = 300 , 
                        data = {"oxygen":table1_df , "water":table2_df}) :
    """
p : dry air pressure (hPa)
e : water vapour partial pressure (hPa) (total barometric pressure, ptot = p + e)
T : temperature (K).
theta = 300/T
    """
    theta = 300/T
    S     = []
    df    = data[type]
    if "oxygen" in type :
        fi = df.loc[:,"f0"]
        a3 = df.loc[:,"a3"]
        a4 = df.loc[:,"a4"]
        a5 = df.loc[:,"a5"]
        a6 = df.loc[:,"a6"]
        df = a3*10**(-4)*(p*theta**(0.8-a4) + 1.1*e*theta)
        df = np.sqrt( df**2 + 2.25*10**(-6) )
        delta = (a5+a6*theta)*10**(-4)*( p + e )*theta**0.8

    if "water" in type :
        fi = df.loc[:,"f0"]
        b3 = df.loc[:,"b3"]
        b4 = df.loc[:,"b4"]
        b5 = df.loc[:,"b5"]
        b6 = df.loc[:,"b6"]
        df = b3*10**(-4)*(p*theta**b4 + b5*e*theta**b6)
        df = 0.535*df + np.sqrt( 0.217*df**2 + 2.1316*10**(-12)*fi**2/theta )
        delta = 0
    f = freq
    F = f/fi * ( (df-delta*(fi-f))/((fi-f)**2+df**2) + (df-delta*(fi+f))/((fi+f)**2+df**2) )
    return(F)


def ND(freq,p,e,T) :
    """
p : dry air pressure (hPa)
e : water vapour partial pressure (hPa) (total barometric pressure, ptot = p + e)
T : temperature (K).
theta = 300/T
d : width paramater for Debye spectrum
    """
    f     = freq
    theta = 300/T
    d     = 5.6*10**(-4)*( p + e )*theta**0.8
    ND    = freq * p * theta **2 * (6.14*10**(-5)/(d*(1+(f/d)**2) + 1.4*10**(-12)*p*theta**1.5)/(1+1.9*10**(-5)*f**1.5) )
    return ( ND )

def NbisN(freq,p,e,T) :
    # ND( f ) is the dry continuum due to pressure-induced nitrogen absorption
    nd = ND(freq,p,e,T)
    return( nd )

def NbisO(freq,p,e,T, bNitrogen=True ) :
    # Oxygen vapour peaks
    # Sum_i,oxygen Si * Fi
    # S is the strength of the oxygen line
    # F is the lineshape of the oxygen line
    # ND( f ) is the dry continuum due to pressure-induced nitrogen absorption
    #    often added here by convention
    S = linestrength_S("oxygen",p,e,T)
    F = lineshape_F(freq,"oxygen",p,e,T)
    NbO = np.dot(S,F) + ND(freq,p,e,T) if bNitrogen else 0 
    return( NbO )

def NbisWater(freq,p,e,T) :
    # Water vapour peaks
    # Sum_i,h2o Si * Fi
    # S is the strength of the water line
    # F is the lineshape of the water line
    #
    S = linestrength_S("water",p,e,T)
    F = lineshape_F(freq,"water",p,e,T)
    return( np.dot(S,F) )

def gasattenuation(freq,p,e,T) :
    gamma = 0.1820 * freq * ( NbisO(freq,p,e,T) + NbisWater(freq,p,e,T) )    
    return ( gamma )

if __name__=='__main__' :
    print("GAS")
    print( table1_df )
    print( table2_df )
    env = environments_ITU_R_P_835( Z=0.1 ) # 10 km
    p   = env[0]
    e   = env[1]
    T   = env[2]
    freqs = [f for f in range(1000)]
    att = []
    for f in freqs :
        att.append( gasattenuation(f,p,e,T) )

    import matplotlib.pyplot as plt
    plt.semilogy(freqs,att)
    plt.show()

    if False :
        # PLOT THE ENVIRONMENT AT DIFFERENT HEIGHTS IN KM
        Z = [h for h in range(0,100)]
        T,P = [],[]
        for z in Z :
            env = environments_ITU_R_P_835( Z=z )
            T.append(env[2])
            P.append(env[0])
        import matplotlib.pyplot as plt
        plt.semilogx(P,Z)
        plt.show()
