''' '''
import numpy as np
import matplotlib.pyplot as plt
from math import factorial
def winLoc(H, winType ):
  '''
  Returns the WW 
  '''
  datBlack = [    [0.42,	0.5,		0.08,		0.],
                  [7938. / 18608,	9240. / 18608,	1430. / 18608,	0.0],
                  [0.42323 ,		0.49755 ,		0.07922 ,		0.0],
                  [0.44959,		0.49364 ,		0.05677 ,		0.0],
                  [0.35875 ,		0.48829 ,		0.14128 ,		0.01168],
                  [0.40217 ,		0.49703 ,		0.09392 ,		0.00183]]
  nameBlack = ('Edged Blackman', 'Exact Blackman', 'Harris 3 term -67', 'Harris 3 term -61', 'Harris 4 term -92', 'Harris 4 term -74') 
  sCutBlack = ('EBL', 'ExBL', 'HA67', 'HA61', 'HA92', 'HA74' ) 
  # if needed insert the type   *************************
  i=np.arange(0,H)

  if winType==0: #no win
    win=np.ones(H)
    name='Top Hat'
    sCut='TH'
  elif winType==1: #Nogueira
    WH = abs((H - 1) / 2.0 - i) / H
    win= (4*WH*WH - 4*WH+1)
    name='Nogueira 1999'
    sCut='NOG'
  elif winType==2: # Blackman ridotta
    WH = (i+1) / (H+1)
    win = (0.42 - 0.5*np.cos(2*np.pi*WH)+0.08*np.cos(4*np.pi*WH))
    name='Blackman'
    sCut='BL'
  elif winType==3: # doppia finestra quadrata
    lar = 0.25
    WH = abs((H - 1) / 2.0 - i) / H
    win =np.ones(H)      # if needed insert the type   *************************
    win[WH > lar]= 0 
    name='Double TH'
    sCut='DTH'
  elif winType==4: # doppia finestra quadrata bordo 1
    win =np.ones(H)     # if needed insert the type   *************************
    win[0]= 0
    win[-1]= 0 
    name='Edged TH'
    sCut='ETH'
  elif 5<=winType<=10: # Various Windows
    ind = winType - 5
    WH = i / (H - 1)
    win = (datBlack[ind][0]-datBlack[ind][1]*np.cos(2*np.pi*WH)+datBlack[ind][2]*np.cos(4*np.pi*WH)-datBlack[ind][3]*np.cos(6*np.pi*WH))
    name=nameBlack[ind] 
    sCut=sCutBlack[ind]
  elif winType==21: # Nogueira  new
    WH = abs((H - 1) / 2.0 - i) / H
    win = ((3*(4*WH*WH - 4*WH+1)+.15*np.cos(4*np.pi*WH)+.2*np.cos(6*np.pi*WH)+.1*np.cos(8*np.pi*WH)+.05*np.cos(10*np.pi*WH)) / 3.5)
    name='Nogueira 2005'
    sCut='NOG05'
  elif winType==22: # Bartlett ridotta  diversa da triang di matlab
      ii=np.arange(0,(H+2) / 2-1,dtype=int)
      WH = 2*abs((ii+1) / (H+1))
      win=np.ones(H)
      win[H - ii-1] =WH
      win[ii] = WH
      name='Triangular'
      sCut='TR'
  elif winType==23: # Hann ridotta
    WH = (i+1) / (H+1)
    win = (0.5 - 0.5*np.cos(2*np.pi*WH))
    name='Hann'
    sCut='HA'
  elif 101<=winType<=200: # Gaussian
    alpha = ((winType - 100.0) / 10.0)
    WH = (2*alpha*((H - 1) / 2.0 - i) / H)
    win = np.exp(-0.5*WH*WH)
    #as=sprintf(f'{alpha,"#.1f"}')
    name='Gaussian '+f'{alpha:.1f}'
    sCut='GA'+f'{alpha:.1f}'
  return (win,name,sCut)

def mtfSpline(o,n):
  '''
    n=order
    see Frequency Domain Analysis of B-Spline  Interpolation 
    by Zeljka MihajloviC*, Alan Goluban**, Mario Zagar**
    doi:10.1109/ISIE.1999.801783
    and of course Unser 1993 a and b
    '''
  k=np.arange(0,n+1)
  fa=lambda k:np.array([factorial(v) for v in k ])

  bSpline =lambda x: np.sum(( ((-1)**k)*(n+1)*((x+(n+1)/2-k)**n)*np.heaviside(x+(n+1)/2-k,1) )/(fa(k)*fa(n+1-k)))
  aa=bSpline(0)
  for kk in np.arange(1,n/2+1):
    aa=aa+2*bSpline(kk)*np.cos(2*np.pi*kk*o)
  mtf=np.sinc(o)**(n+1)/aa
  return mtf

def  mtfPIV1(Wa,FlagWindowing,hWb, FlagCalcVel,Wc, IntVel, oMaxC, WBase,nPointPlot,Niter,flagLambda):
  '''
  # Input **********************************
  #Niter=[2 10 40 1000   inf]# Number of final iteration
  #nPointPlot=1000
  #WBase=16# scaltura plot
  # A  correlation window
  #Wa=32
  #FlagWindowing=0  # Weighting window for the correlation map (0=TopHat 1= Nogueira 2=Blackman 3=top hat at 50#).
  # B  weighted  average
  #FlagCalcVel=0    # Weighting window for absolute velocity (0=TopHat, 1=Nogueira, 2=Blackman,...)
  #hWb=4# Half-width of the filtering window (0=window dimension).
  # C dense predictor 
  #IntVel=1      # Type of interpolation of the velocity (1=bilinear, 52-70 Bspline)
  #Wc=4 #Grid distance (overlap)
  #oMax=0.5 # frequenza massima per c (legata all'overlap ov/lambda) non penso che abbia senso oltre 0,5 perchè 
            # andremmo oltre Nyquist
  # flagLambda se =1 allora equispazia lambda con un massimo di WBase*4 normalizza il grafico fra 
  # same as done by PIV software
  '''
  if(np.mod(hWb,2)==1): #dispari
    Wb=2*hWb-1
  else:
    if hWb==0:
      Wb=Wa
    else:
      Wb=2*hWb
   


  # Windows 
  [WinA,nameA,sCutA]=winLoc(Wa, FlagWindowing)
  WinA=WinA/sum(WinA)
  [WinB,nameB,sCutB]=winLoc(Wb, FlagCalcVel)
  WinB=WinB/sum(WinB)

  # omega W/lambda
  if flagLambda:
    lam=np.linspace(Wc/oMaxC,WBase*4,nPointPlot)
    oC=Wc/lam
  else:
    oC=np.linspace(oMaxC/nPointPlot,oMaxC,nPointPlot)
    lam=Wc/oC
  oBase=oC*WBase/Wc
  oA=oC*Wa/Wc
  oB=oC*Wb/Wc
  # Windows MTF *******
  MTFWin=lambda Win,o,W: np.sum((np.tile(Win,(o.size,1))*np.cos(np.reshape(o, (-1, 1))*(2*np.pi*(np.arange(1,W+1)-W/2-0.5))/W)),1)
  a=MTFWin(WinA,oA,Wa)
  b=MTFWin(WinB,oB,Wb)



  '''
  for FlagWindowing=[0:10 21:23 101:10:200]
    figure (1)clf
    [WinA,nameA,sCutA]=winLoc(Wa, FlagWindowing)
    plot(WinA)
    title ([nameA,' -- ',sCutA])
    pause
  end
  '''
  # Interpolation MTF *******
  if (IntVel==1):
    c=(np.sin(np.pi*oC)/(Wc*np.sin(np.pi*oC/Wc)))**2
    order=1
  elif (52<=IntVel<=70):
      c=mtfSpline(oC,IntVel-50)
      order=IntVel-50
  else:
    c=1+0*oC
    order=-1

  # verify stability **********************
  flagUnstable=0
  if (np.sum(abs(c*(b-a))>1)!=0):
    flagUnstable=1


  # calc MTF **********************
  MTF=np.zeros((Niter.size,oBase.size))
  for j in range(Niter.size):
    ii=Niter[j]
    if(ii==np.inf):
        MTF[j]=a/(1-(c*(b-a)))
    else:
        MTF[j]=a*(1-(c*(b-a))**ii)/(1-(c*(b-a)))

  return (WinA,nameA,sCutA,Wa,WinB,nameB,sCutB,Wb, order,flagUnstable,  oBase,lam,MTF,a,b,c)


def main():
  ''' main '''
  
  
  '''
  FlagWindowing=2
  Wa=15
  for FlagWindowing in np.concatenate ((np.arange(0,11) ,[21,22,23], np.arange(101,200,10))):
    (win,name,sCut)=winLoc(Wa,FlagWindowing ) 
    plt.title (name+' -- '+sCut)
    plt.plot(win,'.-')  # Plot some data on the axes.
    plt.grid()
    plt.show()
  '''
  Niter=np.array([1, 2, 3, np.inf])## Number of final iteration
  nPointPlot=1000
  WBase=16# scalatura plot

  # A  correlation window
  Wa=32
  FlagWindowing=0 # Weighting window for the correlation map (0=TopHat 1= Nogueira 2=Blackman 3=top hat at 50#).
  # B  weighted  average
  FlagCalcVel=0  # Weighting window for absolute velocity (0=TopHat, 1=Nogueira, 2=Blackman,...)
  hWb=8# Half-width of the filtering window (0=window dimension).
  # C dense predictor 
  IntVel=52  # Type of interpolation of the velocity (1=bilinear, 52-70 Bspline)
  Wc=4#  Grid distance (overlap)
  #   end input *********************************************

  oMax=0.5 # frequenza massima per c (legata all'overlap ov/lambda) non penso che abbia senso oltre 0,5 perchè 
          # andremmo oltre Nyquist
    
  WBase=2*Wa# scalatura plot the maximmum lambda is 4 *WBase in this case we are using a maximum of 8*Wa
  flagLambda=1
  
  (WinA,nameA,sCutA,Wa,WinB,nameB,sCutB,Wb,order,flagUnstable,oBase,lam,MTF,a,b,c)= mtfPIV1(Wa,FlagWindowing,hWb, FlagCalcVel,Wc, IntVel, oMax, WBase,nPointPlot,Niter,flagLambda)


  
  fig, ax = plt.subplots()
  ax.plot(oBase,a,'b')#plt.hold on grid on
  ax.plot(oBase,b,'r')
  ax.plot(oBase,c)
  ax.grid()
  fig2, ax2= plt.subplots()
  ax2.plot(WinA)
  ax2.plot(WinB)
  ax2.grid()


  fig4, ax4= plt.subplots()
  ax4.grid()
  ax4.plot(lam,MTF.T)
  ax4.set(xlim=(1, max(lam)), ylim=(-.50, 1),)


  fig3, ax3= plt.subplots()
  ax3.grid()
  ax3.plot(oBase,MTF.T)
  ax3.set(xlim=(0, max(oBase)), ylim=(-.50, 1),)

  plt.show()
  


if __name__ == "__main__":

  main()
