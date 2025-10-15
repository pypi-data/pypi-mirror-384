''' PaIRS_UniNa  '''

import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='PaIRS_UniNa',description="To launch PaIRS use: \npython -m PaIRS_UniNa  ",formatter_class=argparse.RawDescriptionHelpFormatter)
    # for now only Optional arguments: clean is evaluted first if not set then debug is checked a
    # necessario che sia presente 
    #parser.add_argument("echo", help="echo the string you use here") 
    parser.add_argument("-calvi","-CalVi" , help="Launch CalVi",action="store_true")
    parser.add_argument("-c", "--clean" ,help="Clean the configuration file before starting",action="store_true")
    parser.add_argument("-d", "--debug" ,help="Launch in debug mode",action="store_true")

    
    
  
    args = parser.parse_args()

    #print(args)
    
    if args.calvi:
        from PaIRS_UniNa import CalVi    as modulo
    else:
        from PaIRS_UniNa import PaIRS as modulo
    
    if args.clean:
        #print ('Clean')
        modulo.cleanRun()
    elif args.debug:
        modulo.debugRun()
        #print ('Debug')
    else:
        #print ('Normal start ')
        modulo.run()
    

    

    '''from PaIRS_UniNa import PaIRS
    if FlagRun==0:
        PaIRS.run()
    elif FlagRun==1:
        PaIRS.cleanRun()
    elif FlagRun==2:
        PaIRS.debugRun()'''
    
