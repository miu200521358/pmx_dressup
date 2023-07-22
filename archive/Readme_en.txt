----------------------------------------------------------------
----------------------------------------------------------------

　PmxDressup

　　ver1.00.00

　　　　　　　　　　　　　　　　　miu200521358

----------------------------------------------------------------
----------------------------------------------------------------


　Thank you for downloading my work.
　Please check the following before using it.

----------------------------------------------------------------


----------------------------------------------------------------
■ Summary
----------------------------------------------------------------

　This tool fits a specified costume to a specified model according to her body shape.
　After some degree of automatic fitting, adjustments can be made to individual bones.

　If the opacity of the material is set to less than 1, it will not be used as a changeable model.

　The following bones will be created for the changeover model
　　All parents, upper body 2, arm twist, hand twist, foot D, knee D, ankle D, toes EX

　[Work required in advance]
　　If there are vertices in the same material that you want to output and those that you do not want to output, please separate the materials.

　[Manual adjustment after output]
　　Set the rigid body group and non-collision group.
　　　　→ If the costume is to be violent, set the rigid body at the base of the costume to be non-collision with the rigid body of the body it is in contact with.
　　Delete lower vertex
　　　　→ Delete vertices as long as they do not cause holes in the model, so that vertices do not penetrate the model and the model becomes lighter.

　【Notes】
　　The weights of the costume models have been slightly altered to clean up the deformation.
　　　This product is not available for costume models for which weight manipulation is not permitted.
　　If the mesh on the arms or other body-covering positions of the costume is weighted with weights other than the quasi-standard bones, it will not be eligible for support


----------------------------------------------------------------
Video distribution
----------------------------------------------------------------

(In preparation)

----------------------------------------------------------------
Included files
----------------------------------------------------------------

　PmxDressup_x.xx.xx.exe ... Tool itself (with language-specific batchs)
　Readme.txt ... Readme
　VMD Sizing Wiki ... Link to Wiki
　Content tree still image ... Link to content tree still image
　Body for mesh filling ... Body (made by VRoid)


----------------------------------------------------------------
Operating environment
----------------------------------------------------------------

　Windows 10/11 64bit
　CPU or GPU running OpenGL 4.4 or higher


----------------------------------------------------------------
Startup
----------------------------------------------------------------

Basically, you can start the exe as it is.

The version with logging outputs a log file in the same location as the exe file path.

The file history can be copied by placing "history.json" in the same hierarchy as the exe.


----------------------------------------------------------------
■　Basic Usage
----------------------------------------------------------------

 1. in the File tab, specify the person model and costume model (motion is optional but heavy...)

 2. open the Settings tab
    - Once you open the settings tab, you can press the output button. 3.

 3. In the Settings tab, the left side of the screen shows the model with basic fitting (height, build, etc.) done.
    - In the upper right corner, you can specify whether or not the material will be output as opacity.
       - Materials with opacity less than 1 will not be output, so please lower the opacity of materials you do not need.
    - In the lower right corner, you can adjust each bone type.
       - X ... Horizontal direction
       - Y ... Vertical direction
       - Z ... Depth direction
    - If there is a mesh with the same bone name but with weights applied to both the person and the costume, the position of the mesh will basically be output according to the person's side.
      However, if you check the box "Bone positions are aligned with costume model", you can force the output to be aligned with the bone positions on the costume side.
      (Especially from the wrist to the tips of the fingers, no fitting is performed, so please select accordingly.)
    - If the "Share settings as skin material" checkbox is checked for both the person and costume skin material, the person's skin material settings will be copied to the costume and the texture color will be matched.

 4. When you have finished fitting, go back to the File tab and click the "Output Costume Model" button.
    - The model will be output with the material, bones, rigid body, etc. adjusted accordingly.
    - If there is a risk of overwriting files, textures, etc. of the original model with the result of the changeover, the output will be aborted.

 Extra
   The model data in the folder "Mesh Compensating Elements" is an element model that I created in VRoid Studio.
   If the person model lacks mesh for areas such as the neck or above the elbows, this model can be loaded as a costume model,
   The fitting results can then be output to use a person model with the necessary mesh filled in.
   There are no restrictions, so please use it if you think it will work.
   If the mesh of the arms or other parts of the costume are weighted with weights other than the semi-standard bones, they are not eligible for support.


----------------------------------------------------------------
In case of problems
----------------------------------------------------------------

　The unzipped file is garbled.
　McAfee detects the presence of a virus.
　If you encounter any of these problems, please refer to the following page to see if the problem can be resolved. (This is the FAQ page for VMD Sizing)

　https://github.com/miu200521358/vmd_sizing/wiki/03.-%E5%95%8F%E9%A1%8C%E3%81%8C%E8%B5%B7%E3%81%8D%E3%81%9F%E5%A0%B4%E5%90%88

　If you still cannot solve the problem, please report it in the community.


----------------------------------------------------------------
Community
----------------------------------------------------------------

　Nikoni community: https://com.nicovideo.jp/community/co5387214

　　VMD sizing, motion supporter, and other homebrew tools.
　　You can try out the beta version of the site as soon as possible.
　　I would like to be able to follow up if the tool does not work properly.
　　The site is closed, but it is auto-approved, so please feel free to join!

----------------------------------------------------------------
Terms of use, etc.
----------------------------------------------------------------

　Required Information.

　　- If you publish or distribute a model with a change of clothes, please give credit where credit is due.
　　- In the case of Nico Nico Douga, please register the still image (to be created) for the tree in the contents tree.
　　　 - If you register as a parent in the content tree, credit is optional.
　　- If you distribute your models to the general public, please clearly state the credit only in the distribution notice (video, etc.) and register the model in the content tree.
　　　 - It is not necessary to request a credit statement for works that use the model in question.

　Optional

　　- The following actions are permitted within the scope of the original model's terms and conditions.

　　- Adjustment and modification of changed models
　　　 - In the case of distributed models, please make sure that the terms of use allow for alterations.
　　- Posting videos of models on video-sharing sites, SNS, etc.
　　　 - Posting of models with costume settings created in progress is also acceptable.
　　　 - However, if the original model's terms and conditions stipulate a posting destination, age restrictions, etc., models dressed with this tool will also be subject to those terms and conditions.
　　- Distribution of models to an unspecified number of people
　　　 - Only self-made models or models for which distribution to an unspecified number of people is permitted.

　Prohibited items

　　- Please refrain from the following acts regarding this tool and generated models

　　- Actions that are outside the scope of the rules of the original model.
　　- Complete self-made statement.
　　- Actions that may cause inconvenience to the rights holders.
　　- Actions that are intended to defame or slander others (regardless of whether they are two-dimensional or three-dimensional).

　　- The following conditions are not prohibited, but we ask that you take them into consideration
　　　 - Use of images that contain excessive violence, obscenity, romantic, bizarre, political or religious expressions (R-15 or above).

　　　 - Please make sure to check the terms and conditions of the original model before using the work.
　　　 - Please be sure to check the scope of the terms and conditions of the original model, etc., before using the work.

　　- Please note that "commercial use" is not prohibited in this tool, but is prohibited in PMXEditor.

　Disclaimer

　　- Please use at your own risk.
　　- The author assumes no responsibility for any problems caused by the use of this tool.


----------------------------------------------------------------
Source code library
----------------------------------------------------------------

This tool is written in python, and the following libraries are used and included.

numpy (https://pypi.org/project/numpy/)
bezier (https://pypi.org/project/bezier/)
numpy-quaternion (https://pypi.org/project/numpy-quaternion/)
wxPython (https://pypi.org/project/wxPython/)
pyinstaller (https://pypi.org/project/PyInstaller/)

Source code is available on Github. (MIT License)
However, copyright is not waived.

https://github.com/miu200521358/pmx_dressup

Icons are borrowed from icon-rainbow
https://icon-rainbow.com/%E3%83%AF%E3%83%B3%E3%83%94%E3%83%BC%E3%82%B9%E3%81%AE%E7%84%A1%E6%96%99%E3%82%A2%E3%82%A4%E3%82%B3%E3%83 %B3%E7%B4%A0%E6%9D%90-2/


----------------------------------------------------------------
Credits
----------------------------------------------------------------

　Tool name: PmxDressup
　Author: miu or miu200521358

　http://www.nicovideo.jp/user/2776342
　Twitter: @miu200521358
　Mail: garnet200521358@gmail.com


----------------------------------------------------------------
History
----------------------------------------------------------------

