
import bcrypt, sys
print("bcrypt file:", getattr(bcrypt, "__file__", None))
print("__about__:", getattr(bcrypt, "__about__", None))
print("__version__:", getattr(bcrypt, "__version__", None))
print("'__about__' in dir(bcrypt)?", "__about__" in dir(bcrypt))


