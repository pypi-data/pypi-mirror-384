#-------------------------------------------------------------------------------------
#  Author: Junjun Guo
#  E-mail: guojj@tongji.edu.cn/guojj_ce@163.com
#    Date: 05/02/2020
#-------------------------------------------------------------------------------------
import time 
import numpy as np
import matplotlib.pyplot as plt
from fiberGenerate import CircleSection, PolygonSection

def _size_figure(outSideNode):
    """
    calculate the window width and height
    input：outSideNode-utside line internodes dict {1:(x1,x2),2(x2,y2),...,n:(xn,yn)}
    output：figSize-figure window width and height list [w,h]
    """
    dictValues=outSideNode.values()
    xValues = [each1[0] for each1 in dictValues]
    yValues = [each2[1] for each2 in dictValues]
    minX,maxX=min(xValues),max(xValues)
    minY,maxY=min(yValues),max(yValues)
    w=np.abs(maxX-minX)
    h=np.abs(maxY-minY)
    return w,h

def circleSection(diameter,
                  coverThick,
                  outbarD,
                  outbarDist,
                  coreSize,coverSize,
                  plot=False,
                  inD=None,
                  inBarD=None,
                  inBarDist=None,
                  file=None):
    """

    Parameters:
       outD # the diameter of the outside circle
       coverThick # the thinckness of the cover concrete
       outbarD # outside bar diameter
       outbarDist # outside bar space
       coreSize # the size of core concrete fiber
       coverSize # the size of cover concrete fiber
       plot #plot the fiber or not plot=True or False
       inD # the diameter of the inner circle,if not inD=None
       inBarD # inside bar diameter, if not inBarD=None
       inBarDist # inside bar space,if not inBarDist=None

    Output:
    ---coreFiber,coverFiber,barFiber #core concrete, cover concrete anb bar fibers information
       for eaxample coreFiber=[(y1,z1,area1),(y2,y2,area2),...], y1,z1 is the fiber coordinate values in loacal y-z plane
       area1 is the fiber area

    #######################---solid circle example---#####################
    outD=2  # the diameter of the outside circle
    coverThick=0.1  # the thinckness of the cover concrete
    outbarD=0.03  # outside bar diameter
    outbarDist=0.15  # outside bar space
    coreSize=0.2  # the size of core concrete fiber
    coverSize=0.2  # the size of cover concrete fiber
    plotState=False  # plot the fiber or not plot=True or False
    corFiber,coverFiber,barFiber=circleSection(outD, coverThick, outbarD, outbarDist, coreSize, coverSize,plotState)

    ##################---circle with a hole example---####################
    outD = 2  # the diameter of the outside circle
    coverThick = 0.06  # the thinckness of the cover concrete
    outbarD = 0.03  # outside bar diameter
    outbarDist = 0.15  # outside bar space
    coreSize = 0.1  # the size of core concrete fiber
    coverSize = 0.1  # the size of cover concrete fiber
    plotState = True  # plot the fiber or not plot=True or False
    inD =1 # the diameter of the inside circle
    inBarD=0.03 # inside bar diameter
    inBarDist=0.15 # inside bar space
    corFiber, coverFiber, barFiber = circleSection(outD, coverThick, outbarD, outbarDist, coreSize, coverSize,
                                                   plotState,inD,inBarD,inBarDist)
    """
    circle = CircleSection(coverThick, diameter, inD)

    # generate core concrete fiber elements
    coreFiber, pointsPlot, trianglesPlot = circle.core_mesh(coreSize)
    
    # generate cover concrete fiber elements
    coverFiber, coverXListPlot, coverYListPlot, xBorderPlot, yBorderPlot = circle.cover_mesh(coverSize)
    
    # generate the bar fiber elements
    barFiber, barXListPlot, barYListPlot = circle.rebar_mesh(outbarD, outbarDist, inBarD, inBarDist)

    if plot == True:
        outSideNode = {1: (-diameter,-diameter), 2: (diameter,diameter)}
        fig = plt.figure(figsize=_size_figure(outSideNode))
        ax = fig.add_subplot(111)

        for eachx, eachy in zip(*circle.exterior()):
            ax.plot(eachx, eachy, "r", linewidth=1, zorder=2)

        ax.triplot(pointsPlot[:, 0], pointsPlot[:, 1], trianglesPlot)

        for coverx, covery in zip(coverXListPlot, coverYListPlot):
            ax.plot(coverx, covery, "r", linewidth=1, zorder=2)
        for borderx, bordery in zip(xBorderPlot, yBorderPlot):
            ax.plot(borderx, bordery, "r", linewidth=1, zorder=2)

        for barx, bary in zip(barXListPlot, barYListPlot):
            ax.scatter(barx, bary, s=10, c="k", zorder=3)

        if file is not None:
            plt.savefig(file+".eps")
            plt.savefig(file+".jpg")
        plt.show()
    else:
        pass
    return coreFiber,coverFiber,barFiber


def polygonSection(outSideNode,outSideEle,coverThick,coreSize,coverSize,outBarD,outBarDist,\
                   plot=False,autorebar_mesh=True,userBarNodeDict=None,userBarEleDict=None,inSideNode=None,\
                   inSideEle=None,inBarD=None,inBarDist=None, sectionName=None):
    """
    Input:
    ---outSideNode # the outside vertexes consecutively numbering and coordinate values in local y-z plane in dict container
    ---outSideEle  # the outside vertexes loop consecutively numbering in dict container
    ---coverThick  # the thinck of the cover concrete
    ---coreSize  # the size of the core concrete fiber elements
    ---coverSize   # the size of the cover concrete fiber elements
    ---outBarD  # outside bar diameter
    ---outBarDist  # outside bar space
    ---plot=True # plot the fiber or not plot=True or False
    ---autorebar_mesh=True # generate the bar fiber automatically, otherwise manually provide the bar divide information
    ---userBarNodeDict=None# {1:(y1,z1),2:(y2,z2),...}
    ---userBarEleDict=None #{1:(nodeI,nodeJ,barD,barDist)}
    ---inSideNode #the inside vertexes consecutively numbering and coordinate values in local y-z plane in list container
    ---inSideEle # the inside vertexes loop consecutively numbering in list container
    ---inBarD #inside bar diameter
    ---inBarDist #inside bar space
    Output:
    ---coreFiber,coverFiber,barFiber #core concrete, cover concrete anb bar fibers information
       for eaxample coreFiber=[(y1,z1,area1),(y2,y2,area2),...], y1,z1 is the fiber coordinate values in loacal y-z plane
       area1 is the fiber area
    """
    sect = PolygonSection(outSideNode, outSideEle, inSideNode, inSideEle)

    originalNodeListPlot = sect.sectPlot()  # [([x1,x2],[y1,y2]),([].[])]
    outLineList, coverlineListPlot = sect.coverLinePlot(coverThick)

    if inSideNode==None:
        sect = PolygonSection(outSideNode, outSideEle)
        originalNodeListPlot = sect.sectPlot()  # [([x1,x2],[y1,y2]),([].[])]
        outLineList, coverlineListPlot = sect.coverLinePlot(coverThick)
        coreFiber, pointsPlot, trianglesPlot = sect.core_mesh(coreSize, outLineList)
        coverFiber, outNodeReturnPlot, inNodeReturnPlot = sect.cover_mesh(coverSize, coverThick)
        if autorebar_mesh==True:
            barFiber, barXListPlot, barYListPlot = sect.rebar_mesh(outBarD, outBarDist, coverThick)
        elif autorebar_mesh==False:
            barFiber, barXListPlot, barYListPlot=sect.userrebar_mesh(userBarNodeDict,userBarEleDict)
        else:
            raise ValueError("Please input True or False!")

    else:
        sect = PolygonSection(outSideNode, outSideEle, inSideNode, inSideEle)
        originalNodeListPlot = sect.sectPlot()
        outLineList, coverlineListPlot = sect.coverLinePlot(coverThick)
        inLineList, innerLineListPlot = sect.plot_inner_edge(coverThick)
        coreFiber, pointsPlot, trianglesPlot = sect.core_mesh(coreSize, outLineList, inLineList)
        coverFiber, outNodeReturnPlot, inNodeReturnPlot = sect.cover_mesh(coverSize, coverThick)
        if autorebar_mesh==True:
            barFiber, barXListPlot, barYListPlot = sect.rebar_mesh(outBarD, outBarDist, coverThick, inBarD, inBarDist)
        elif autorebar_mesh==False:
            barFiber, barXListPlot, barYListPlot=sect.userrebar_mesh(userBarNodeDict,userBarEleDict)
        else:
            raise TypeError("Please input True or False!")


    if inSideNode is None and plot==True:
        w, h = _size_figure(outSideNode)
        fig = plt.figure(figsize=(w, h))
        ax = fig.add_subplot(111)
        coverColor = "r"
        coreColor = "b"
        lineWid = 1
        barMarkSize = 20
        barColor = "k"
        for each1 in originalNodeListPlot:
            ax.plot(each1[0], each1[1], coverColor, lineWid, zorder=0)
        for each2 in coverlineListPlot:
            ax.plot(each2[0], each2[1], coverColor, lineWid, zorder=1)
        ax.triplot(pointsPlot[:, 0], pointsPlot[:, 1], trianglesPlot, c=coreColor, lw=lineWid)
        for i1 in range(len(outNodeReturnPlot) - 1):
            ax.plot([inNodeReturnPlot[i1][0], outNodeReturnPlot[i1][0]],
                    [inNodeReturnPlot[i1][1], outNodeReturnPlot[i1][1]],
                    coverColor, linewidth=lineWid, zorder=0)
        ax.scatter(barXListPlot, barYListPlot, s=barMarkSize, c=barColor, linewidth=lineWid, zorder=2)
        
        if sectionName is not None:
            plt.savefig(sectionName+".eps")
            plt.savefig(sectionName+".jpg")
        plt.show()

    elif inSideNode!=None and plot==True:

        w, h = _size_figure(outSideNode)
        fig = plt.figure(figsize=(w, h))
        ax = fig.add_subplot(111)
        coverColor = "r"
        coreColor = "b"
        lineWid = 1
        barMarkSize = 20
        barColor = "k"
        for each1 in originalNodeListPlot:
            ax.plot(each1[0], each1[1], coverColor, lineWid, zorder=0)
        for each2 in coverlineListPlot:
            ax.plot(each2[0], each2[1], coverColor, lineWid, zorder=1)
        for each3 in innerLineListPlot:
            ax.plot(each3[0], each3[1], coverColor, lineWid, zorder=1)
        ax.triplot(pointsPlot[:, 0], pointsPlot[:, 1], trianglesPlot, c=coreColor, lw=lineWid)
        for i1 in range(len(outNodeReturnPlot) - 1):
            ax.plot([inNodeReturnPlot[i1][0], outNodeReturnPlot[i1][0]],
                    [inNodeReturnPlot[i1][1], outNodeReturnPlot[i1][1]],
                    coverColor, linewidth=lineWid, zorder=0)
        ax.scatter(barXListPlot, barYListPlot, s=barMarkSize, c=barColor, linewidth=lineWid, zorder=2)
        if sectionName is not None:
            plt.savefig(sectionName+".eps")
            plt.savefig(sectionName+".jpg")
        plt.show()


    return coreFiber,coverFiber,barFiber



if __name__ == "__main__":
    ###################---solid circle---################
    #
    outD=2  # the diameter of the outside circle
    coverThick=0.1  # the thinckness of the cover concrete
    outbarD=0.03  # outside bar diameter
    outbarDist=0.15  # outside bar space
    coreSize=0.2  # the size of core concrete fiber
    coverSize=0.2  # the size of cover concrete fiber
    plotState=True  # plot the fiber or not plot=True or False
    corFiber,coverFiber,barFiber=circleSection(outD, coverThick, outbarD, outbarDist, 
                                               coreSize, coverSize,plotState)
    ###################---circle with a hole
    #
    outD = 2  # the diameter of the outside circle
    coverThick = 0.06  # the thinckness of the cover concrete
    outbarD = 0.03  # outside bar diameter
    outbarDist = 0.15  # outside bar space
    coreSize = 0.1  # the size of core concrete fiber
    coverSize = 0.1  # the size of cover concrete fiber
    plotState = True  # plot the fiber or not plot=True or False
    inD =1 # the diameter of the inside circle
    inBarD=0.03 # inside bar diameter
    inBarDist=0.15 # inside bar space
    corFiber, coverFiber, barFiber = circleSection(outD, coverThick, outbarD, outbarDist, 
                                                   coreSize, coverSize,
                                                   plotState,inD,inBarD,inBarDist)
    # ############---solid polygon section
    #
#     # the outside vertexes consecutively numbering and coordinate values in local y-z plane in dict container
    outSideNode = {1: (3.5, 3), 2: (1.5, 5), 3: (-1.5, 5), 4: (-3.5, 3), 5: (-3.5, -3), 6: (-1.5, -5), 7: (1.5, -5),
                   8: (3.5, -3)}
#     # the outside vertexes loop consecutively numbering in dict container
    outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 1)}
    coverThick = 0.06  # the thinck of the cover concrete
    coreSize = 0.2  # the size of the core concrete fiber elements
    coverSize = 0.3  # the size of the cover concrete fiber elements
    outBarD = 0.032  # outside bar diameter
    outBarDist = 0.2  # outside bar space
    plotState=True  # plot the fiber or not plot=True or False
    autorebar_mesh=True #if false provide the barControlNodeDict and barEleDict
    userBarNodeDict=None
    userBarEleDict=None
    coreFiber,coverFiber,barFiber=polygonSection(outSideNode, outSideEle, coverThick, coreSize, coverSize,\
                                        outBarD, outBarDist,plotState,autorebar_mesh)

    #
    # polygon with one hole section user bar mesh example
    #
    # the outside vertexes consecutively numbering and coordinate values in local y-z plane in dict container
    outSideNode = {1: (2.559, 2.1), 
                   2: (-2.559, 2.1), 
                   3: (-2.559, 1.6), 
                   4: (-3.059, 1.6), 
                   5: (-3.059, -1.6),
                   6: (-2.559, -1.6), 
                   7: (-2.559, -2.1), 
                   8: (2.559, -2.1), 
                   9: (2.559, -1.6), 
                   10: (3.059, -1.6), 
                   11: (3.059, 1.6),
                   12: (2.559, 1.6)}

    # the outside vertexes loop consecutively numbering in dict container
    outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 9), 9: (9, 10),\
                  10: (10, 11), 11: (11, 12), 12: (12, 1)}

    # the inside vertexes consecutively numbering and coordinate values in local y-z plane in list container
    inSideNode = [{1: (1.809, 1.35), 2: (-1.809, 1.35), 3: (-2.309, 0.85), 4: (-2.309, -0.85), 5: (-1.809, -1.35), \
                   6: (1.809, -1.35), 7: (2.309, -0.85), 8: (2.309, 0.85)}] ##(None)
    # the inside vertexes loop consecutively numbering in dict container
    inSideEle = [{1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 5), 5: (5, 6), 6: (6, 7), 7: (7, 8), 8: (8, 1)}]
    coverThick = 0.06  # the thinck of the cover concrete
    coreSize = 0.2  # the size of the core concrete fiber elements
    coverSize = 0.3  # the size of the cover concrete fiber elements
    outBarD = 0.032  # outside bar diameter(None)
    outBarDist = 0.2  # outside bar space (None)
    plotState=True  # plot the fiber or not plot=True or False
    autorebar_mesh=False #if false provide the barControlNodeDict and barEleDict

    userBarNodeDict = {
        1: (2.975, 1.516), 
        2: (2.475, 1.516), 
        3: (2.475, 2.016), 
        4: (-2.475, 2.016), 
        5: (-2.475, 1.516),
        6: (-2.975, 1.516),
        7: (-2.975, -1.516), 
        8: (-2.475, -1.516), 
        9: (-2.475, -2.016), 
        10: (2.475, -2.016),
        11: (2.475, -1.516),
        12: (2.975, -1.516)
    }
    
    userBarEleDict={
        1: (1, 2,0.01,0.2), 2: (2, 3,0.01,0.2), 3: (3, 4,0.01,0.2), 4: (4, 5,0.01,0.2),\
        5: (6, 5,0.01,0.2), 6: (5, 2,0.01,0.2), 7: (7, 8,0.01,0.2), 8: (8, 9,0.01,0.2), 9: (9, 10,0.01,0.2),
        10: (10, 11,0.01,0.2), 11: (12, 11,0.01,0.2), 12: (11, 8,0.01,0.2),\
    }

    inBarD=0.032  # inside bar diameter (None)
    inBarDist=0.2  # inside bar space (None)
    coreFiber,coverFiber,barFiber = polygonSection(
            outSideNode, outSideEle, 
            coverThick, coreSize, coverSize,
            outBarD, outBarDist,plotState,autorebar_mesh,userBarNodeDict,userBarEleDict,\
            inSideNode,inSideEle,inBarD,inBarDist)

    # ############---polygon with three holes section example---###########
    outSideNode = {1: (0, 0), 2: (7, 0), 3: (7,3), 4: (0, 3)}
    # the outside vertexes loop consecutively numbering in dict container
    outSideEle = {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4,1)}
    # the inside vertexes consecutively numbering and coordinate values in local y-z plane in list container
    inSideNode = [
        {1: (1, 1), 2: (2, 1), 3: (2, 2), 4: (1, 2)},
        {1: (3, 1), 2: (4, 1), 3: (4, 2), 4: (3, 2)},
        {1: (5, 1), 2: (6, 1), 3: (6, 2), 4: (5, 2)}]
    # the inside vertexes loop consecutively numbering in dict container
    inSideEle = [{1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)},
                 {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)},
                 {1: (1, 2), 2: (2, 3), 3: (3, 4), 4: (4, 1)}]

    coverThick = 0.06  # the thinck of the cover concrete
    coreSize = 0.2  # the size of the core concrete fiber elements
    coverSize = 0.3  # the size of the cover concrete fiber elements
    outBarD = 0.032  # outside bar diameter
    outBarDist = 0.2  # outside bar space
    plotState = True  # plot the fiber or not plot=True or False
    autorebar_mesh=True #if false provide the barControlNodeDict and barEleDict
    userBarNodeDict=None
    userBarEleDict=None
    inBarD=0.032  # inside bar diameter (None)
    inBarDist=0.2  # inside bar space (None)
    coreFiber,coverFiber,barFiber=polygonSection(
            outSideNode, outSideEle, coverThick, coreSize, coverSize,
            outBarD, outBarDist,plotState,autorebar_mesh,userBarNodeDict,userBarEleDict,
            inSideNode,inSideEle,inBarD,inBarDist
    )
    
    # print(help(polygonSection))






