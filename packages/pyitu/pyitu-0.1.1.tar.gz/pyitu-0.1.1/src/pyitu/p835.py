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
import numpy as np

__desc__=""" Reference atmospheres """

def atmosphere_environment( H=None , Z=None ):
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
