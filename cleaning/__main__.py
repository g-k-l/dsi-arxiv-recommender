import sys
from .pipeline import main

if len(sys.argv) > 1:
    main(sys.argv[1])
else:
    main()