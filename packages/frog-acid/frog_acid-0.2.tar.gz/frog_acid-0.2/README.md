# Acid the only thing i am making which i am going to use

## Installation
> Error 404
> 
> wtf happened
> 
> acid is not availve for pip yet
> 
> ohhh yeah i forgot ok sooooo... i tihnk we need to go manuly
>
> ok here is the step by step guide copy this because this repo is going to be froged
>
> ok so download it and yeet the folder to ... wait lemme find it real quie... ... ... yeah i found it
>
>`
>    C:\Users\i_will_not_share\AppData\Local\Programs\Python\Python312\Lib\site-packages
>`

## Intro

>   ### Intro
>
>   Ok now it is kinda ok.
>
>   In simple words acid is a wrapper around some tools like pygame and opengl and numpy what about math that is my own code kinda.
>
>   How to use it lets see.
>    
>   to import you just:
>
>```python
>      import acid.pythontwo.window.window as WW # (or whatever you like)
>```
>
># A WAR IS ABOUT TO START SO IF YOU DON'T WANT TO DIE GO BELOW THW WAR

-------

>   now that example was for 2D but what about 3D- (Shut up no body cares we will add docs for 3D later because i am lazy AF bois) you made me sad ( -_•)▄︻テحكـ━一💥 yeah now you ded
> 
>   (the guy who told shut up) "sir they have gun and trying to attack us send backup" (dies)
> 
>   (the backup) ( -_•)▄︻テحكـ━一💥 ( -_•)▄︻テحكـ━一💥 ( -_•)▄︻テحكـ━一💥 ( -_•)▄︻テحكـ━一💥 ( -_•)▄︻テحكـ━一💥 ( -_•)▄︻テحكـ━一💥 ( -_•)▄︻テحكـ━一💥 ( -_•)▄︻テحكـ━一💥 ( -_•)▄︻テحكـ━一💥
> 
>   (me) "did i really need to die like this" (dies)
> 
>   (me) "go frog live your life 🐸🐸🐸🐸🐸"
> 
>   (the frog got guns and now trying to rule the world with frog os frog builder and frogedit) (only microsoft remains who will die)
>
> ---
> 
>   if you have quetions look at the code
>
>   now to start it we just say to it:
>
> ``` python
>      window = WW.window((800, 600), "test for dummies")
>
>      window.init()
>```
>   ### Game loop
>
>   but if you run it, it will show you a screen for a milli-second,
>   so to solve that you make a while loop and put 2 things in it 3 is you wanna fill the screen with something else color (wtf was that grammar my guy)
>
>   example code again bois:
>```python
>        while window.brorunning:
>            window.loop()
>            window.mupdate()
>``` 
>   ### Creating Shapes
>
>   (i will do this part later) well that was past tenses
>
>   (i hate my life while writing a README f#######K)
>
>   what was i suppose to do... oh yeah shapes right yeah lets make this quike because i need to go to a wedding of some unknown person
>
>   to draw a rectangle:
> 
>   inside the gmae loop after window.loop()
> ``` python
>     window.MakeRect(*pos, *size, *color)
> ```
>   to make a circle i forgot half of the things
> 
>   inside the game loop after window.loop()
> ``` python
>     window.MakeCircle(*pos, *radius, *color)
>```
>   and i think i have dementia because i forgot lines bruh:
>``` python
>     window.Makeline((*point1), (*point2), (*color))
>```
>   and i think i have dementia because i forgot pixel bruh:
>``` python
>     window.Makepixel(*pos, *color)
>```
>   ### Images
>
>   is this entire thing outdated i think so because there is still 3D, ui and maths left when will i make readme for them. it will take me ages am i alive  myr92 rfqjtmfgvb hdzfjgdvrbjhvzx
>
>   ok what is the topic Images right images are arrays of 3 pixels red, green and blue (someone) you were talking aboput how to display a image in acid
>
>   thanks for reminding
>
>   this is the code:
>``` python
>     window.MakeImage(*pos, *size, *img_loc)
> ```
