#!/usr/bin/env python3
import numpy as np
import pandas as pd


def area_heron_x2(a, b, c):
    s = (a+b+c)/2
    if min(s-a, s-b, s-c) <= 0:
        return np.nan
    else:
        return np.sqrt(s*(s-a)*(s-b)*(s-c))


class circle:
    def __init__(self, r, x):
        self.r = r
        self.x = x
        self.S = np.pi * r * r


class circle_overlap:
    def __init__(self, c1, c2, d):

        fct = 1
        S_square = area_heron_x2(c1.r, c2.r, d)

        if np.isnan(S_square):   # cannot make inner triangle

            alpha1 = np.nan
            d1 = np.nan
            h = np.nan

            if d < c1.r:
                overlap = 1.
            else:
                overlap = 0.

        else:  # can make inner triangle
            # https://tjkendev.github.io/procon-library/python/geometry/circles_intersection_area.html

            theta1 = np.arccos((c1.r**2 + d**2 - c2.r**2) / (2 * c1.r * d))
            theta2 = np.arccos((c2.r**2 + d**2 - c1.r**2) / (2 * c2.r * d))

            S_fan = c1.r**2 * theta1 + c2.r**2 * theta2
            S_and = S_fan - S_square

            # complete overlap ratio
            S_or = c1.S + c2.S - S_and
            overlap = min(S_and / S_or, 1.0)

            # smaller-side overlap ratio
            #S_small = min(c1.S, c2.S)
            #overlap = min(S_and / S_small, 1.0)

        self.overlap = overlap


def test():

    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    r1, r2 = 500, 600

    ds = np.arange(100, 1151, 50)
    overs = []
    alpha1s = []
    d1s = []
    hs = []

    for d in ds:

        c1 = circle(r=r1, x=0)
        c2 = circle(r=r2, x=d)
        o = cirlce_overlap(c1, c2, d)
        overs.append(o.overlap)
        alpha1s.append(o.alpha1)
        d1s.append(o.d1)
        hs.append(o.h)


    for i, d in enumerate(ds):

        print(f'{d=}')
        
        ax = plt.axes()
        C1 = patches.Circle(xy=(0, 500), radius=r1, fc='none', ec='tab:blue')
        C2 = patches.Circle(xy=(d, 500), radius=r2, fc='none', ec='tab:blue')
        ax.add_patch(C1)
        ax.add_patch(C2)
        ax.plot(0, 500, marker='.', c='tab:blue')
        ax.plot(d, 500, marker='.', c='tab:blue')
        ax.plot([d1s[i], d1s[i]], [500-hs[i], 500+hs[i]], c='r')
        ax.set_aspect('equal')
        ax.set_xlim([-700,1250])
        ax.set_ylim([-200, 1200])
        ax.set_title(f'O={overs[i]:.3f}')
        plt.savefig(f'fig/cc_d{d}.png')
        plt.close()

        ax = plt.axes()
        ax.plot(ds, overs)
        ax.plot(ds[i], overs[i], '.r')
        plt.savefig(f'fig/overs_{d}.png')
        plt.close()

        '''ax = plt.axes()
        ax.plot(ds, np.array(alpha1s)/np.pi)
        ax.plot(ds[i], alpha1s[i]/np.pi, '.r')
        plt.savefig(f'fig/alpha1s_d{d}.png')
        plt.close()'''
        

if __name__ == '__main__':
    test()
