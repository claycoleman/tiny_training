################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (12.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_bitmask.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_mask.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_bitmask.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_mask.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_bitmask.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_mask.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_bitmask.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_mask.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_bitmask.c \
../Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_mask.c \
../Src/TinyEngine/codegen/Source/genModel.c 

C_DEPS += \
./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_bitmask.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_mask.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_bitmask.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_mask.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_bitmask.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_mask.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_bitmask.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_mask.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_bitmask.d \
./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_mask.d \
./Src/TinyEngine/codegen/Source/genModel.d 

OBJS += \
./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_bitmask.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_mask.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_bitmask.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_mask.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_bitmask.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_mask.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_bitmask.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_mask.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_bitmask.o \
./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_mask.o \
./Src/TinyEngine/codegen/Source/genModel.o 


# Each subdirectory must supply rules for building sources it contributes
Src/TinyEngine/codegen/Source/%.o Src/TinyEngine/codegen/Source/%.su Src/TinyEngine/codegen/Source/%.cyclo: ../Src/TinyEngine/codegen/Source/%.c Src/TinyEngine/codegen/Source/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m7 -std=c11 -g -DSTM32F746xx -c -I../Src -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/include" -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/include/arm_cmsis" -I"/Users/ccoleman/Developer/harvard/tinyml/tiny_training/Src/TinyEngine/codegen/Include" -I../Inc -I../Drivers/STM32F7xx_HAL_Driver/Inc -I../Drivers/BSP/STM32746G-Discovery -I../Drivers/CMSIS/Include -I../Drivers/CMSIS/Device/ST/STM32F7xx/Include -I../TinyEngine/include -Og -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@"  -mfpu=fpv5-sp-d16 -mfloat-abi=hard -mthumb -o "$@"

clean: clean-Src-2f-TinyEngine-2f-codegen-2f-Source

clean-Src-2f-TinyEngine-2f-codegen-2f-Source:
	-$(RM) ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq.d ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq.o ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq.su ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_bitmask.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_bitmask.d ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_bitmask.o ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_bitmask.su ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_mask.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_mask.d ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_mask.o ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride1_inplace_CHW_fpreq_mask.su ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq.d ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq.o ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq.su ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_bitmask.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_bitmask.d ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_bitmask.o ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_bitmask.su ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_mask.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_mask.d ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_mask.o ./Src/TinyEngine/codegen/Source/depthwise_kernel3x3_stride2_inplace_CHW_fpreq_mask.su ./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq.d ./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq.o ./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq.su ./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_bitmask.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_bitmask.d ./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_bitmask.o ./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_bitmask.su ./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_mask.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_mask.d ./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_mask.o ./Src/TinyEngine/codegen/Source/depthwise_kernel5x5_stride1_inplace_CHW_fpreq_mask.su ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq.d ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq.o ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq.su ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_bitmask.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_bitmask.d ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_bitmask.o ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_bitmask.su ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_mask.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_mask.d ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_mask.o ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride1_inplace_CHW_fpreq_mask.su ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq.d ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq.o ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq.su ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_bitmask.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_bitmask.d ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_bitmask.o ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_bitmask.su ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_mask.cyclo ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_mask.d ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_mask.o ./Src/TinyEngine/codegen/Source/depthwise_kernel7x7_stride2_inplace_CHW_fpreq_mask.su ./Src/TinyEngine/codegen/Source/genModel.cyclo ./Src/TinyEngine/codegen/Source/genModel.d ./Src/TinyEngine/codegen/Source/genModel.o ./Src/TinyEngine/codegen/Source/genModel.su

.PHONY: clean-Src-2f-TinyEngine-2f-codegen-2f-Source

