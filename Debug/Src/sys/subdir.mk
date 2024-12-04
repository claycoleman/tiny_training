################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (12.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Src/sys/_io.c \
../Src/sys/stubs.c 

C_DEPS += \
./Src/sys/_io.d \
./Src/sys/stubs.d 

OBJS += \
./Src/sys/_io.o \
./Src/sys/stubs.o 


# Each subdirectory must supply rules for building sources it contributes
Src/sys/%.o Src/sys/%.su Src/sys/%.cyclo: ../Src/sys/%.c Src/sys/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m7 -std=c11 -g -DSTM32F746xx -c -I../Src -I"/Users/kennethchen/Desktop/HBS GSAS/MIT Tiny ML/tiny_training/Src/TinyEngine/include" -I"/Users/kennethchen/Desktop/HBS GSAS/MIT Tiny ML/tiny_training/Src/TinyEngine/include/arm_cmsis" -I"/Users/kennethchen/Desktop/HBS GSAS/MIT Tiny ML/tiny_training/Src/TinyEngine/codegen/Include" -I../Inc -I../Drivers/STM32F7xx_HAL_Driver/Inc -I../Drivers/BSP/STM32746G-Discovery -I../Drivers/CMSIS/Include -I../Drivers/CMSIS/Device/ST/STM32F7xx/Include -I../TinyEngine/include -Og -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@"  -mfpu=fpv5-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Src-2f-sys

clean-Src-2f-sys:
	-$(RM) ./Src/sys/_io.cyclo ./Src/sys/_io.d ./Src/sys/_io.o ./Src/sys/_io.su ./Src/sys/stubs.cyclo ./Src/sys/stubs.d ./Src/sys/stubs.o ./Src/sys/stubs.su

.PHONY: clean-Src-2f-sys

