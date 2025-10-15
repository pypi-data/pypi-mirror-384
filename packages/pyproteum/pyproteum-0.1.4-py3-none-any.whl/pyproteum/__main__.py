from pyproteum import testnew, tcase, mutagen, exemuta, mutaview
import sys

if __name__ == '__main__':
	del sys.argv[0]
	if sys.argv ==[]:
		print('You should use one of the pyproteum commands.')
	else:	
		match sys.argv[0]: 
			case 'testnew':
				testnew.main()
			case 'tcase':
				tcase.main()
			case 'mutagen':
				mutagen.main()
			case 'exemuta':
				exemuta.main()
			case 'mutaview':
				mutaview.main()
			case _:
				print(f'Not found statement {sys.argv[0]}')

